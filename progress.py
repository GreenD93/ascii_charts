def progress(value, total=100, width=30, char="█", empty="░", title=None):
    
    """
    Render a horizontal ASCII progress bar.

    Parameters
    ----------
    value : int | float
        현재 값 (진행 상황).
    total : int | float, default=100
        최대 값 (게이지의 기준).
    width : int, default=30
        진행바 전체 길이(문자 수).
    char : str, default="█"
        채워진 구간을 표시할 문자.
    empty : str, default="░"
        비어 있는 구간을 표시할 문자.
    title : str, optional
        진행바 상단에 표시할 제목 문자열.

    Returns
    -------
    str
        ASCII 문자열로 표현된 진행바.

    Notes
    -----
    - total이 0 이하이면 진행률은 0%로 처리됨.
    - 출력 형식:  
      ```
      [█████░░░░░░░░░░░░░░░░░░] 16.7% (5/30)
      ```
    - title이 주어지면 진행바 위에 중앙 정렬된 제목이 출력됨.
    """

    frac = value / total if total > 0 else 0
    filled = int(round(frac * width))
    bar = char * filled + empty * (width - filled)
    lines = []
    if title:
        lines.append(title.center(width + 10, "="))
        lines.append("")
    lines.append(f"[{bar}] {frac*100:.1f}% ({value}/{total})")
    
    return "\n".join(lines)


from typing import Iterable, Dict, List, Tuple, Union, Optional

def progress_multi(
    items: Union[Dict[str, Tuple[float, float]], Iterable[Tuple[str, float, float]]],
    width: int = 30,
    char: str = "█",
    empty: str = "░",
    title: Optional[str] = None,
    label_side: str = "right",        # "left" | "right" | "both" | "none"
    show_percent: bool = True,
    show_fraction: bool = True,
    percent_digits: int = 1,
    sort: Optional[str] = None,       # None | "asc" | "desc" | "label"
    gap: int = 1,
    label_min_width: Optional[int] = None,
    per_item_chars: Optional[List[str]] = None,
    right_pad_min: int = 0,
    right_content: str = "meta"       # ✅ "meta" | "label" | "both" | "none"
) -> str:
    # --- 입력 정규화 ---
    if isinstance(items, dict):
        data = [(k, v[0], v[1]) for k, v in items.items()]
    else:
        data = list(items)
    if not data:
        return "No data."

    def fmt_meta(v: float, t: float) -> str:
        t = float(t)
        frac = (v / t) if t > 0 else 0.0
        parts = []
        if show_percent:
            parts.append(f"{frac*100:.{percent_digits}f}%")
        if show_fraction:
            def _fmt(x):
                xf = float(x)
                return f"{int(xf)}" if xf.is_integer() else f"{xf}"
            parts.append(f"({_fmt(v)}/{_fmt(t)})")
        return " ".join(parts) if parts else ""

    def glyph_for(i: int) -> str:
        if per_item_chars:
            return per_item_chars[i % len(per_item_chars)]
        return char

    # 진행률/메타 선계산
    tmp: List[Tuple[str, float, float, float, str]] = []
    for label, v, t in data:
        t = float(t)
        frac = (v / t) if t > 0 else 0.0
        meta = fmt_meta(v, t)
        tmp.append((str(label), float(v), t, frac, meta))

    # 정렬
    if sort == "asc":
        tmp.sort(key=lambda x: x[3])
    elif sort == "desc":
        tmp.sort(key=lambda x: x[3], reverse=True)
    elif sort == "label":
        tmp.sort(key=lambda x: x[0])

    # 왼쪽 라벨 폭
    if label_side in ("left", "both"):
        max_label = max((len(t[0]) for t in tmp), default=0)
        left_w = max(label_min_width or 0, max_label)
    else:
        left_w = 0

    # 오른쪽 내용(라벨/메타/둘다) 구성 및 폭
    def right_text(label: str, meta: str) -> str:
        if right_content == "meta":
            return meta
        if right_content == "label":
            return label
        if right_content == "both":
            return f"{meta} {label}" if meta else label
        return ""  # "none"

    right_candidates = []
    if label_side in ("right", "both"):
        for label, _v, _t, _f, meta in tmp:
            right_candidates.append(right_text(label, meta))
        right_w = max([right_pad_min] + [len(s) for s in right_candidates]) if right_candidates else 0
    else:
        right_w = 0

    gap_str = " " * max(0, gap)
    lines: List[str] = []

    # 제목
    if title:
        est_width = left_w + (gap if left_w else 0) + 2 + width + (gap if right_w else 0) + right_w
        lines.append(title.center(max(est_width, width) + 10, "="))
        lines.append("")

    # 본체
    for i, (label, v, t, frac, meta) in enumerate(tmp):
        filled = int(round(frac * width)) if width > 0 else 0
        filled = max(0, min(width, filled))
        bar = glyph_for(i) * filled + empty * (width - filled)

        parts = []
        if left_w and label_side in ("left", "both"):
            parts.append(label.ljust(left_w))
            parts.append(gap_str)

        parts.append(f"[{bar}]")

        if right_w and label_side in ("right", "both"):
            rtxt = right_text(label, meta)
            parts.append(gap_str)
            parts.append(rtxt.rjust(right_w))  # 고정 폭 우측 정렬

        lines.append("".join(parts).rstrip())

    return "\n".join(lines)