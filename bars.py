def bar_horizontal(labels, counts, width=40, glyphs=None,
                         show_percent=True, title=None):
    
    """
    Render a horizontal ASCII bar chart.

    Parameters
    ----------
    labels : list[str]
        각 막대에 해당하는 카테고리 이름 리스트.
    counts : list[int | float]
        각 라벨에 대응하는 값 리스트. labels와 길이가 같아야 함.
    width : int, default=40
        막대 최대 길이(문자 수). 값이 클수록 가로로 더 긴 막대 출력.
    glyphs : list[str], optional
        각 막대에 사용할 문자 집합. 제공하지 않으면 기본 팔레트 사용.
    show_percent : bool, default=True
        True이면 각 항목 오른쪽에 퍼센트(%)를 함께 표시.
    title : str, optional
        차트 상단에 표시할 제목 문자열.

    Returns
    -------
    str
        ASCII 문자열로 그려진 가로형 바 차트.

    Notes
    -----
    - labels와 counts의 길이는 반드시 같아야 함.
    - counts 합계가 0 이하이면 `"No data."` 반환.
    - 범례(legend)는 각 항목의 글리프와 라벨 매핑을 하단에 표시.
    - show_percent=False이면 값만 출력되고, 퍼센트는 생략됨.
    """
    
    total = sum(counts)
    if total <= 0:
        return "No data."
    
    n = len(labels)
    if n == 0 or n != len(counts):
        return "Invalid input."
    
    # 기본 글리프 팔레트
    default_glyphs = ["█","■","▲","◆","●","✦","▒","░","*","+"]
    if glyphs is None or len(glyphs) == 0:
        glyphs = default_glyphs
    
    lines = []
    
    # 제목 처리
    if title:
        lines.append(title.center(width + 20, "="))
        lines.append("")
    
    # 막대 출력
    for idx, (lab, val) in enumerate(zip(labels, counts)):
        frac = val / total
        bar_len = int(round(frac * width))
        ch = glyphs[idx % len(glyphs)]  # 항목별 글리프 선택
        bar = ch * bar_len
        if show_percent:
            label_str = f"{lab} {val} ({frac*100:.1f}%)"
        else:
            label_str = f"{lab} {val}"
        lines.append(f"{label_str.ljust(15)} | {bar}")
    
    # 범례 추가 (글리프-라벨 매핑)
    legend = " | ".join(f"{glyphs[i % len(glyphs)]} {labels[i]}" for i in range(n))
    lines.append(legend)
    
    return "\n".join(lines)

def bar_vertical(labels, counts, max_height=10, glyphs=None,
                       show_percent=True, width=None, title=None,):
    
    """
    Render a vertical ASCII bar chart.

    Parameters
    ----------
    labels : list[str]
        각 막대에 해당하는 카테고리 이름 리스트.
    counts : list[int | float]
        각 라벨에 대응하는 값 리스트. labels와 길이가 같아야 함.
    max_height : int, default=10
        막대의 최대 높이(줄 수).
    glyphs : list[str], optional
        각 항목의 막대에 사용할 문자 집합. 제공하지 않으면 기본 팔레트 사용.
        길이가 부족하면 순환하여 적용.
    show_percent : bool, default=True
        막대 하단에 퍼센트(%) 라벨을 표시할지 여부.
    title : str, optional
        차트 상단에 표시할 제목 문자열.
    width : int, optional
        제목 가운데 정렬에 사용할 기준 폭. 지정하지 않으면 차트 실제 폭을 사용.

    Returns
    -------
    str
        ASCII 문자열로 그려진 세로형 바 차트.

    Notes
    -----
    - labels와 counts의 길이는 반드시 같아야 함.
    - counts 합계가 0 이하이면 `"No data."` 반환.
    - 막대 두께는 고정값 2, 막대 사이 간격은 1칸.
    - show_percent=True일 경우 막대 하단에 각 항목 비율이 정수(%)로 표시됨.
    - 차트 맨 아래에는 값, 라벨, 그리고 글리프 ↔ 라벨 범례가 표시됨.
    """
    
    total = sum(counts)
    if total <= 0:
        return "No data."
    n = len(labels)
    if n == 0 or n != len(counts):
        return "Invalid input."

    # 기본 글리프 팔레트
    default_glyphs = ["█","■","▲","◆","●","✦","▒","░","*","+"]
    if glyphs is None or len(glyphs) == 0:
        glyphs = default_glyphs
    # 막대 두께/간격
    bar_thickness = 2
    gap = 1

    # 비율 → 막대 높이
    heights = [int(round((v/total) * max_height)) for v in counts]

    # 차트 폭 계산 (제목 정렬 용)
    chart_width = n * (bar_thickness + gap)
    if width is None:
        width = chart_width

    lines = []

    # 제목 처리 (요청하신 형식 그대로)
    if title:
        lines.append(title.center(width + 20, "="))
        lines.append("")

    # 본체(위→아래)
    for level in range(max_height, 0, -1):
        row_parts = []
        for h, g in zip(heights, [glyphs[i % len(glyphs)] for i in range(n)]):
            if h >= level:
                row_parts.append(g * bar_thickness)
            else:
                row_parts.append(" " * bar_thickness)
            row_parts.append(" " * gap)
        lines.append("".join(row_parts).rstrip())

    # 퍼센트 라벨(막대 아래)
    if show_percent:
        percents = [f"{(v/total)*100:.0f}%" for v in counts]
        # 각 칸 가운데 정렬(막대 두께+간격 기준)
        cell_w = bar_thickness + gap
        lines.append("".join(p.center(cell_w) for p in percents).rstrip())

    # 값 라벨
    cell_w = bar_thickness + gap
    lines.append("".join(str(v).center(cell_w) for v in counts).rstrip())

    # 이름 라벨
    lines.append("".join(l.center(cell_w) for l in labels).rstrip())

    # 범례(글리프 ↔ 라벨)
    legend = " | ".join(f"{(glyphs[i % len(glyphs)])} {labels[i]}" for i in range(n))
    lines.append(legend)

    return "\n".join(lines)

def stacked_bar(labels, counts_list, sublabels=None, width=40, glyphs=None, title=None):
    
    """
    Render a horizontal stacked ASCII bar chart.

    Parameters
    ----------
    labels : list[str]
        각 막대(행)의 이름 리스트.
    counts_list : list[list[int | float]]
        각 막대별 값들의 리스트.  
        예: [[10, 20, 30], [5, 15, 25]] → 두 개의 행, 각 행은 세 구간으로 구성.
    sublabels : list[str], optional
        항목 이름 리스트. 범례(legend)에 사용됨.
        counts_list의 내부 리스트 길이와 일치해야 함.
    width : int, default=40
        전체 막대(행)의 최대 너비(문자 단위).
    glyphs : list[str], optional
        각 항목(세그먼트)에 사용할 문자 집합. 없으면 기본 팔레트 사용.
        항목 수보다 짧으면 순환 적용됨.
    title : str, optional
        차트 상단에 표시할 제목 문자열.

    Returns
    -------
    str
        ASCII 문자열로 그려진 가로형 누적 막대 그래프.

    Notes
    -----
    - 각 행(`labels[i]`)에 대해 `counts_list[i]`의 값들을 합산해 막대를 구성.
    - 값이 0인 경우 해당 행은 빈 막대로 출력됨.
    - sublabels를 지정하면 범례가 마지막 줄에 표시됨.
    - width는 전체 막대 길이를 제한하며, 값 비율에 따라 각 세그먼트 길이가 결정됨.
    """
    
    default_glyphs = ["█","■","▲","◆","●","✦","▒","░","*","+"]
    if glyphs is None or len(glyphs) == 0:
        glyphs = default_glyphs
    
    lines = []
    if title:
        lines.append(title.center(width + 20, "="))
        lines.append("")
    
    for lab, counts in zip(labels, counts_list):
        total = sum(counts)
        if total == 0:
            bar = ""
        else:
            bar_parts = []
            for idx, val in enumerate(counts):
                frac = val / total
                seg_len = int(round(frac * width))
                bar_parts.append(glyphs[idx % len(glyphs)] * seg_len)
            bar = "".join(bar_parts)
        lines.append(f"{lab.ljust(10)} | {bar}")
    
    if sublabels:
        legend = " | ".join(f"{glyphs[i % len(glyphs)]} {sublabels[i]}" for i in range(len(sublabels)))
        lines.append(legend)
    
    return "\n".join(lines)