from __future__ import annotations

import argparse
import re
from collections import defaultdict
from itertools import combinations
from pathlib import Path


EPSILON = "epsilon"
EPSILON_ALIASES = {"epsilon", "eps", "e", "ε", "ϵ"}
PRODUCTION_RE = re.compile(r"^\s*([A-Z])\s*(?:->|→)\s*(.+?)\s*$")
SYMBOL_RE = re.compile(r"^[A-Za-z0-9]+$|^(?:epsilon|eps|e|ε|ϵ)$")


class GrammarError(ValueError):
    pass


def normalize_body(body: str) -> str:
    cleaned = body.strip().replace(" ", "")
    if cleaned in EPSILON_ALIASES:
        return EPSILON
    if not SYMBOL_RE.fullmatch(cleaned):
        raise GrammarError(f"cuerpo de produccion invalido: {body!r}")
    return cleaned


def load_grammar(path: Path) -> dict[str, set[str]]:
    grammar: dict[str, set[str]] = defaultdict(set)
    lines = path.read_text(encoding="utf-8").splitlines()

    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        match = PRODUCTION_RE.fullmatch(line)
        if not match:
            raise GrammarError(
                f"Linea {line_number} mal escrita: {raw_line!r}. "
                "Use el formato A -> aB | epsilon."
            )

        head, bodies = match.groups()
        alternatives = bodies.split("|")
        if any(not alternative.strip() for alternative in alternatives):
            raise GrammarError(
                f"Linea {line_number} mal escrita: hay una alternativa vacia."
            )

        for body in alternatives:
            grammar[head].add(normalize_body(body))

    if not grammar:
        raise GrammarError("El archivo no contiene producciones validas.")

    return dict(grammar)


def nullable_symbols(grammar: dict[str, set[str]]) -> tuple[set[str], list[tuple[str, str, str]]]:
    nullable: set[str] = set()
    trace: list[tuple[str, str, str]] = []
    changed = True

    while changed:
        changed = False
        for head, bodies in grammar.items():
            for body in sorted(bodies):
                is_direct_epsilon = body == EPSILON
                is_composed_nullable = (
                    body != EPSILON
                    and body
                    and all(symbol.isupper() and symbol in nullable for symbol in body)
                )

                if (is_direct_epsilon or is_composed_nullable) and head not in nullable:
                    nullable.add(head)
                    reason = "produce epsilon directamente" if is_direct_epsilon else (
                        f"produce {body}, formado solo por simbolos anulables"
                    )
                    trace.append((head, body, reason))
                    changed = True

    return nullable, trace


def variants_without_nullable(body: str, nullable: set[str]) -> set[str]:
    positions = [
        index for index, symbol in enumerate(body)
        if symbol.isupper() and symbol in nullable
    ]
    variants = {body}

    for amount in range(1, len(positions) + 1):
        for removed_positions in combinations(positions, amount):
            removed = set(removed_positions)
            candidate = "".join(
                symbol for index, symbol in enumerate(body) if index not in removed
            )
            if candidate:
                variants.add(candidate)

    return variants


def remove_epsilon_productions(
    grammar: dict[str, set[str]],
) -> tuple[dict[str, set[str]], set[str], list[tuple[str, str, set[str]]], list[tuple[str, str, str]]]:
    nullable, nullable_trace = nullable_symbols(grammar)
    new_grammar: dict[str, set[str]] = defaultdict(set)
    expansion_trace: list[tuple[str, str, set[str]]] = []

    for head, bodies in grammar.items():
        for body in sorted(bodies):
            if body == EPSILON:
                continue
            variants = variants_without_nullable(body, nullable)
            new_grammar[head].update(variants)
            expansion_trace.append((head, body, variants))

    return dict(new_grammar), nullable, expansion_trace, nullable_trace


def format_body(body: str) -> str:
    return "epsilon" if body == EPSILON else body


def print_grammar(grammar: dict[str, set[str]]) -> None:
    for head in sorted(grammar):
        bodies = " | ".join(format_body(body) for body in sorted(grammar[head]))
        print(f"{head} -> {bodies}")


def process_file(path: Path) -> None:
    print("=" * 72)
    print(f"Archivo: {path}")
    print("=" * 72)

    grammar = load_grammar(path)
    print("\nGramatica original:")
    print_grammar(grammar)

    simplified, nullable, expansion_trace, nullable_trace = remove_epsilon_productions(grammar)

    print("\n1) Simbolos anulables encontrados:")
    if not nullable_trace:
        print("   No se encontraron simbolos anulables.")
    else:
        for head, body, reason in nullable_trace:
            print(f"   - {head}: por {head} -> {format_body(body)} ({reason})")
    print(f"   Conjunto anulable: {{{', '.join(sorted(nullable))}}}")

    print("\n2) Nuevas producciones generadas:")
    for head, body, variants in expansion_trace:
        nullable_count = sum(
            1 for symbol in body if symbol.isupper() and symbol in nullable
        )
        print(
            f"   - {head} -> {body}: m = {nullable_count}, "
            f"casos = {2 ** nullable_count}, produce "
            f"{{{', '.join(sorted(variants))}}}"
        )

    print("\n3) Gramatica sin producciones epsilon:")
    print_grammar(simplified)
    print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Elimina producciones epsilon de gramaticas libres de contexto."
    )
    parser.add_argument(
        "files",
        nargs="+",
        type=Path,
        help="Archivos de texto con producciones, por ejemplo gramatica1.txt.",
    )
    args = parser.parse_args()

    try:
        for path in args.files:
            process_file(path)
    except (OSError, GrammarError) as error:
        print(f"Error: {error}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
