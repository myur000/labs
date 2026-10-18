"""Создает воспроизводимый учебный лог. Реальные серверы не используются."""

from pathlib import Path


def log_line(ip, path, status):
    return (
        f'{ip} - - [19/Oct/2026:00:00:00 +0700] '
        f'"GET {path} HTTP/1.1" {status} 123 "-" "StudyClient/1.0"\n'
    )


def main():
    lines = [log_line("192.0.2.10", f"/missing-{i}", 404) for i in range(51)]
    lines += [log_line("198.51.100.20", f"/not-found-{i}", 404) for i in range(50)]
    lines += [log_line("203.0.113.30", "/index.html", 200) for _ in range(3)]
    lines += [log_line("2001:db8::1", "/private", 403)]
    lines += ["Некорректная строка лога\n", log_line("999.1.1.1", "/missing", 404)]
    path = Path(__file__).with_name("sample_access.log")
    path.write_text("".join(lines), encoding="utf-8")
    print(f"Создан {path.name}: {len(lines)} строк.")


if __name__ == "__main__":
    main()
