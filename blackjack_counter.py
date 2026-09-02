#!/usr/bin/env python3
"""Terminal blackjack card counter using Hi-Lo.

Tracks running count, true count, and remaining deck composition.
"""

import argparse
import os
import sys
from collections import Counter

SUITS = "♠♥♦♣"
RANKS = "A23456789TJQK"

HI_LO_VALUES = {
    "2": 1, "3": 1, "4": 1, "5": 1, "6": 1,
    "7": 0, "8": 0, "9": 0,
    "T": -1, "J": -1, "Q": -1, "K": -1, "A": -1,
}

def _parse_card(token):
    token = token.strip().upper()
    if len(token) < 1:
        raise ValueError(f"invalid card: {token!r}")
    rank = token[0]
    suit = token[1] if len(token) > 1 else "?"
    if rank not in RANKS:
        if rank == "1" and len(token) >= 2 and token[1] == "0":
            rank = "T"
            suit = token[2] if len(token) > 2 else "?"
        else:
            raise ValueError(f"unknown rank: {rank}")
    if suit not in SUITS and suit != "?":
        raise ValueError(f"unknown suit: {suit}")
    return rank, suit

def _build_deck(n_decks):
    deck = Counter()
    for _ in range(n_decks):
        for rank in RANKS:
            deck[rank] += 4
    return deck

def _true_count(running, remaining, n_decks):
    if remaining <= 0:
        return 0.0
    decks_left = remaining / 52.0
    return running / decks_left

def _clear():
    if os.name == "nt":
        os.system("cls")
    else:
        sys.stdout.write("\x1b[2J\x1b[H")

def _draw(state, n_decks, total_cards, base_bet=25):
    _clear()
    remaining = sum(state["deck"].values())
    tc = _true_count(state["running"], remaining, n_decks)
    seen = sum(state["seen"].values())
    print(f"Decks: {n_decks}  |  Seen: {seen}/{total_cards}  |  Remaining: {remaining}")
    print(f"Running count: {state['running']:+d}  |  True count: {tc:+.2f}")
    units = max(1, int(tc))
    bet = base_bet * units
    print(f"Suggested bet: ${bet} ({units} unit{'s' if units != 1 else ''})")
    print()
    print("Remaining composition:")
    for rank in RANKS:
        count = state["deck"][rank]
        bar = "█" * count
        print(f"  {rank:>2}: {count:>2} {bar}")
    print()
    print("Enter cards (or 'reset', 'undo', 'quit'): ", end="", flush=True)

def main():
    parser = argparse.ArgumentParser(
        description="Blackjack card counter (Hi-Lo)",
        usage="python blackjack_counter.py [--decks N] [--base-bet X] [cards...]",
    )
    parser.add_argument("--decks", type=int, default=6, help="number of decks (default 6)")
    parser.add_argument("--base-bet", type=int, default=25, help="base bet in dollars (default 25)")
    parser.add_argument("cards", nargs="*", help="space-separated cards, e.g. 2h 7s AT")
    args = parser.parse_args()

    n_decks = max(1, args.decks)
    total_cards = n_decks * 52
    base_bet = max(1, args.base_bet)

    state = {
        "deck": _build_deck(n_decks),
        "seen": Counter(),
        "running": 0,
        "history": [],
    }

    if args.cards:
        for token in args.cards:
            try:
                rank, suit = _parse_card(token)
            except ValueError as exc:
                print(f"error: {exc}", file=sys.stderr)
                sys.exit(1)
            if state["deck"][rank] <= 0:
                print(f"error: no more {rank} left in shoe", file=sys.stderr)
                sys.exit(1)
            state["deck"][rank] -= 1
            state["seen"][rank] += 1
            state["running"] += HI_LO_VALUES[rank]
            state["history"].append(rank)

    _draw(state, n_decks, total_cards, base_bet)

    while True:
        try:
            line = input()
        except EOFError:
            print()
            break
        line = line.strip()
        if not line:
            _draw(state, n_decks, total_cards, base_bet)
            continue
        if line.lower() in ("q", "quit", "exit"):
            break
        if line.lower() == "reset":
            state["deck"] = _build_deck(n_decks)
            state["seen"] = Counter()
            state["running"] = 0
            state["history"] = []
            _draw(state, n_decks, total_cards, base_bet)
            continue
        if line.lower() == "undo":
            if state["history"]:
                last = state["history"].pop()
                state["deck"][last] += 1
                state["seen"][last] -= 1
                state["running"] -= HI_LO_VALUES[last]
            _draw(state, n_decks, total_cards, base_bet)
            continue

        for token in line.split():
            try:
                rank, suit = _parse_card(token)
            except ValueError as exc:
                print(f"\nerror: {exc}")
                continue
            if state["deck"][rank] <= 0:
                print(f"\nerror: no more {rank} left in shoe")
                continue
            state["deck"][rank] -= 1
            state["seen"][rank] += 1
            state["running"] += HI_LO_VALUES[rank]
            state["history"].append(rank)

        _draw(state, n_decks, total_cards, base_bet)

if __name__ == "__main__":
    try:
        sys.exit(main() or 0)
    except KeyboardInterrupt:
        sys.exit(130)
