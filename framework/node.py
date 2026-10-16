"""Simplified Raft consensus, driven synchronously for teaching.
Nodes: follower -> candidate -> leader. Leader replicates log entries;
a majority confirms an entry is committed."""


class RaftNode:
    def __init__(self, node_id, peers):
        self.id = node_id
        self.peers = peers  # list of other RaftNode
        self.term = 0
        self.voted_for = None
        self.role = "follower"
        self.log = []          # [(term, command)]
        self.commit_index = 0
        self.votes = set()
        self.alive = True

    def _majority(self):
        total = 1 + len(self.peers)
        return total // 2 + 1

    # ---- election ----
    def start_election(self):
        if not self.alive:
            return
        self.term += 1
        self.role = "candidate"
        self.voted_for = self.id
        self.votes = {self.id}
        granted = 0
        for p in self.peers:
            if p.alive and p._vote(self.term, self.id):
                self.votes.add(p.id)
                granted += 1
        if len(self.votes) >= self._majority():
            self.role = "leader"
            self.heartbeat()
        return self.role

    def _vote(self, term, candidate_id):
        if not self.alive:
            return False
        if term < self.term:
            return False
        if term > self.term:
            self.term = term
            self.voted_for = None
        if self.voted_for in (None, candidate_id):
            self.voted_for = candidate_id
            self.role = "follower"
            return True
        return False

    # ---- heartbeats / replication ----
    def heartbeat(self):
        if self.role != "leader" or not self.alive:
            return
        for p in self.peers:
            if p.alive:
                p._become_follower(self.term)

    def _become_follower(self, term):
        if term >= self.term:
            self.term = term
            self.role = "follower"

    def propose(self, command):
        """Leader appends an entry, replicates, commits on majority."""
        if self.role != "leader" or not self.alive:
            return False
        self.log.append((self.term, command))
        entry_index = len(self.log) - 1
        acked = 1
        for p in self.peers:
            if p.alive and p._replicate(self.term, self.log[entry_index]):
                acked += 1
        if acked >= self._majority():
            self.commit_index = entry_index
        return acked >= self._majority()

    def _replicate(self, term, entry):
        if not self.alive or term < self.term:
            return False
        if term > self.term:
            self.term = term
        self.log.append(entry)
        return True

    def crash(self):
        self.alive = False
        self.role = "follower"

    def recover(self):
        self.alive = True
