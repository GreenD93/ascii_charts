def heatmap(matrix, row_labels=None, col_labels=None, glyphs=None, title=None):
    
    """
    Render a text-based heatmap where values are mapped to glyph intensity.

    Parameters
    ----------
    matrix : list[list[int | float]]
        2차원 리스트(행렬 값). 각 내부 리스트는 하나의 행(row)을 나타냄.
    row_labels : list[str], optional
        각 행(row)에 대한 라벨. matrix의 행 개수와 같아야 함.
    col_labels : list[str], optional
        각 열(column)에 대한 라벨. matrix의 열 개수와 같아야 함.
    glyphs : list[str], optional
        값의 크기를 표현할 문자 집합(낮음 → 높음).  
        제공하지 않으면 기본 팔레트 [" ", "·", "░", "▒", "▓", "█"] 사용.
    title : str, optional
        차트 상단에 표시할 제목 문자열.

    Returns
    -------
    str
        ASCII 문자열로 표현된 히트맵.

    Notes
    -----
    - 행렬 내 최소값(vmin)은 glyphs[0], 최대값(vmax)은 glyphs[-1]에 매핑됨.
    - 모든 값이 동일할 경우 vmax = vmin+1 로 처리하여 0으로 나눔 방지.
    - col_labels가 있으면 히트맵 상단에 열 이름이 출력됨.
    - row_labels가 있으면 각 행 앞에 라벨이 출력됨.
    - glyphs의 개수는 농도 단계 수를 결정함.
    """
    
    default_glyphs = [" ", "·", "░", "▒", "▓", "█"]
    if glyphs is None or len(glyphs) == 0:
        glyphs = default_glyphs
    
    flat = [v for row in matrix for v in row]
    vmin, vmax = min(flat), max(flat)
    if vmax == vmin:
        vmax = vmin + 1
    
    def val_to_char(v):
        idx = int((v - vmin) / (vmax - vmin) * (len(glyphs) - 1))
        return glyphs[idx]
    
    lines = []
    if title:
        width = len(matrix[0]) * 2 + 10
        lines.append(title.center(width, "="))
        lines.append("")
    
    # 열 이름
    if col_labels:
        lines.append("     " + " ".join(c.center(2) for c in col_labels))
    
    # 본체
    for i, row in enumerate(matrix):
        row_str = " ".join(val_to_char(v) for v in row)
        if row_labels:
            lines.append(f"{row_labels[i].ljust(4)} {row_str}")
        else:
            lines.append(row_str)
    
    return "\n".join(lines)
