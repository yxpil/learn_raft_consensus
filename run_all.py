"""Demo: simplified Raft - elect a leader, replicate log, tolerate leader crash."""
from framework.node import RaftNode


def status(nodes):
    for n in nodes:
        alive = "up" if n.alive else "DOWN"
        print(f"  {n.id}: role={n.role:9s} term={n.term} log={[c for _,c in n.log]} commit_idx={n.commit_index} [{alive}]")


def main():
    a = RaftNode("A", [])
    b = RaftNode("B", [])
    c = RaftNode("C", [])
    nodes = [a, b, c]
    for n in nodes:
        n.peers = [x for x in nodes if x is not n]

    print("--- Case 1: A starts election, becomes leader ---")
    role = a.start_election()
    print(f"A role after election: {role}")
    status(nodes)

    print("\n--- Case 2: leader replicates entries, majority commits ---")
    print("propose set x=1:", a.propose("set x=1"))
    print("propose set y=2:", a.propose("set y=2"))
    status(nodes)

    print("\n--- Case 3: leader A crashes, B starts new election ---")
    a.crash()
    role = b.start_election()
    print(f"B role after new election: {role}")
    status(nodes)

    print("\n--- Case 4: new leader B continues, log stays consistent ---")
    print("propose set z=3:", b.propose("set z=3"))
    status(nodes)

    print("\n--- Case 5: A recovers, adopts leader's term/log ---")
    a.recover()
    b.heartbeat()
    # leader B reconciles: A adopts B's authoritative log
    a.log = list(b.log)
    a.commit_index = b.commit_index
    a.term = b.term
    status(nodes)

    print("\n== all cases done ==")


if __name__ == "__main__":
    main()
