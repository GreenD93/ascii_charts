def line(
    series_dict,
    max_height=10,
    point_glyphs=None,
    line_glyph="·",
    title=None,
    x_labels=None,
    x_step=2,
    draw_lines=True,
    show_y_axis=True,
    overlap_mode="mark",       # 점 겹침 처리 방식: 'upper'(나중 것 우선) | 'mark'(*로 통합)
    scale="linear",            # 스케일링: 'linear' | 'robust' | 'log' | 'per_series'
    robust_quantiles=(0.05, 0.95),
    log_base=10,
    show_clipped=True,
    clip_mark="^",
    show_series_ranges=True,   # ✅ 각 시리즈의 실제 min..max 표시
    annotate_last=True,        # ✅ 마지막 시점 실제값 오른쪽에 표기
    annotate_indices=None      # ✅ 특정 인덱스들의 실제값 표기 (예: [0, -1])
):
    """
    Render one or more time series as an ASCII line chart.

    Parameters
    ----------
    series_dict : dict[str, list[float]]
        Key는 시리즈 이름, 값은 동일 길이의 데이터 리스트.
        모든 시리즈는 같은 길이를 가져야 함.
    max_height : int, default=10
        차트의 세로 높이(행 수).
    point_glyphs : list[str], optional
        각 시리즈의 점 모양 문자 집합. 제공하지 않으면 기본 팔레트 사용.
    line_glyph : str, default="·"
        점과 점 사이를 연결할 때 사용할 선 문자.
    title : str, optional
        차트 상단에 표시할 제목.
    x_labels : list[str], optional
        x축 라벨. 데이터 길이와 동일해야 함.
    x_step : int, default=2
        x축에서 각 데이터 포인트 간격(열 수).
    draw_lines : bool, default=True
        True면 점 사이를 선으로 연결.
    show_y_axis : bool, default=True
        왼쪽에 y축 눈금을 표시할지 여부.
    overlap_mode : {"upper", "mark"}, default="mark"
        점이 겹쳤을 때 처리 방식.
        - "upper": 나중에 그린 시리즈가 우선.
        - "mark": "*" 로 표시.
    scale : {"linear", "robust", "log", "per_series"}, default="linear"
        값 스케일링 방식.
        - "linear": 전체 min~max 기준 정규화.
        - "robust": 분위수(robust_quantiles) 기반으로 잘라내고 정규화.
        - "log": 로그 스케일(log_base).
        - "per_series": 시리즈별로 개별 min~max 정규화.
    robust_quantiles : tuple(float, float), default=(0.05, 0.95)
        "robust" 스케일링 시 하위/상위 분위수.
    log_base : int, default=10
        "log" 스케일링의 로그 밑(base).
    show_clipped : bool, default=True
        "robust" 스케일에서 잘린(clipped) 값 표시 여부.
    clip_mark : str, default="^"
        잘린 점을 표시할 때 사용할 문자.
    show_series_ranges : bool, default=True
        범례 하단에 각 시리즈의 실제 값 범위(min..max)를 표시할지 여부.
    annotate_last : bool, default=True
        마지막 시점의 실제 값을 차트 아래에 주석으로 표시.
    annotate_indices : list[int], optional
        특정 인덱스 위치의 실제 값을 주석으로 표시.
        음수 인덱스도 지원(-1은 마지막).

    Returns
    -------
    str
        ASCII 텍스트로 렌더링된 선 그래프 전체 문자열.

    Notes
    -----
    - Y축 값은 0~1 사이 정규화된 값으로 매핑되며,
      실제 값 범위는 `show_series_ranges`와 `y_axis_note`에 표시됨.
    - X축 라벨은 데이터 개수와 동일해야 올바르게 표시됨.
    - 겹치는 점의 처리 방식은 `overlap_mode`에 따름.
    """

    # --- 입력 검증 ---
    if not series_dict:
        return "No data."
    keys = list(series_dict.keys())
    n = len(series_dict[keys[0]])
    if n == 0 or any(len(series_dict[k]) != n for k in keys):
        return "All series must have the same length and be non-empty."

    # --- 점 모양 팔레트 ---
    default_glyphs = ["●","■","▲","◆","○","✦","*","+","x","o"]
    if not point_glyphs:
        point_glyphs = default_glyphs

    import math
    eps = 1e-9

    # ─── 스케일링 준비 ───
    all_vals = [v for k in keys for v in series_dict[k]]

    # 분위수 계산 (robust 스케일링용)
    def quantile(arr, q):
        arr = sorted(arr)
        if not arr:
            return 0.0
        pos = (len(arr)-1)*q
        lo = int(math.floor(pos)); hi = int(math.ceil(pos))
        if lo == hi: return arr[lo]
        return arr[lo] + (arr[hi]-arr[lo])*(pos-lo)

    clipped_mask = {k: [False]*n for k in keys}  # robust 스케일링에서 클리핑 여부 기록

    # --- 스케일링 모드별 처리 ---
    if scale == "linear":
        vmin, vmax = min(all_vals), max(all_vals)
        if vmax == vmin: vmax = vmin + 1.0
        def scaler(v, _k=None, _i=None): return (v - vmin) / (vmax - vmin)
        y_axis_note = f"linear  range=[{vmin:.3g}, {vmax:.3g}]"

    elif scale == "robust":
        q_low, q_high = robust_quantiles
        lo, hi = quantile(all_vals, q_low), quantile(all_vals, q_high)
        if hi == lo: hi = lo + 1.0
        def scaler(v, k=None, i=None):
            clipped = False
            cv = v
            # 분위수 밖은 잘라내기
            if v < lo: cv, clipped = lo, True
            elif v > hi: cv, clipped = hi, True
            if k is not None and i is not None: clipped_mask[k][i] = clipped
            return (cv - lo) / (hi - lo)
        y_axis_note = f"robust q=[{q_low*100:.0f}%,{q_high*100:.0f}%] -> [{lo:.3g},{hi:.3g}]"

    elif scale == "log":
        # 로그 스케일: 값이 0 이하일 경우 전체를 shift
        shift = 0.0
        if min(all_vals) <= 0: shift = -min(all_vals) + eps
        log_vals = [math.log(v+shift, log_base) for v in all_vals]
        lvmin, lvmax = min(log_vals), max(log_vals)
        if lvmax == lvmin: lvmax = lvmin + 1.0
        def scaler(v, _k=None, _i=None):
            return (math.log(v+shift, log_base) - lvmin) / (lvmax - lvmin)
        y_axis_note = f"log{log_base} scaled (axis 0..1), shift={shift:.3g}"

    elif scale == "per_series":
        # 각 시리즈별 개별 min~max로 정규화
        minmax = {}
        for k in keys:
            vmin_k, vmax_k = min(series_dict[k]), max(series_dict[k])
            if vmax_k == vmin_k: vmax_k = vmin_k + 1.0
            minmax[k] = (vmin_k, vmax_k)
        def scaler(v, k=None, _i=None):
            vmin_k, vmax_k = minmax[k]
            return (v - vmin_k) / (vmax_k - vmin_k)
        y_axis_note = "per-series normalized (axis 0..1)"
    else:
        return f"Unknown scale: {scale}"

    # 값(0..1)을 캔버스 행(row)로 변환
    def to_row(y01):
        return (max_height - 1) - int(round(y01 * (max_height - 1)))

    width = n * x_step
    canvas = [[" " for _ in range(width)] for _ in range(max_height)]

    # 점 좌표와 원래 값 저장 (주석용)
    series_points = {}

    # ─── 그리기 ───
    for si, key in enumerate(keys):
        vals = series_dict[key]
        pg = point_glyphs[si % len(point_glyphs)]
        pts = []
        for idx, v in enumerate(vals):
            y01 = scaler(v, key, idx)
            col = idx * x_step
            row = to_row(y01)
            pts.append((col, row))
        series_points[key] = (pts, vals)

        # --- 선 연결 ---
        if draw_lines and len(pts) > 1:
            for (c1, r1), (c2, r2) in zip(pts[:-1], pts[1:]):
                dc, dr = c2-c1, r2-r1
                steps = max(abs(dc), abs(dr))
                if steps > 1:
                    for t in range(1, steps):
                        cc = c1 + int(round(dc*t/steps))
                        rr = r1 + int(round(dr*t/steps))
                        if canvas[rr][cc] == " ":
                            canvas[rr][cc] = line_glyph

        # --- 점 찍기 (겹침 처리 포함) ---
        for idx, (col, row) in enumerate(pts):
            mark = pg
            if scale == "robust" and show_clipped and clipped_mask[key][idx]:
                mark = clip_mark   # 클리핑된 점 표시
            if canvas[row][col] == " ":
                canvas[row][col] = mark
            else:
                canvas[row][col] = mark if overlap_mode=="upper" else "*"

    lines = []
    if title:
        lines.append(title.center(width + 12, "="))
        lines.append("")

    # --- 본체 (Y축 포함 여부) ---
    for lvl, row in enumerate(canvas):
        if show_y_axis:
            y01 = 1 - (lvl / (max_height - 1))
            lines.append(f"{y01:6.2f} | " + "".join(row))
        else:
            lines.append("".join(row))

    # --- X축 ---
    xaxis = "-" * width
    lines.append(("       " if show_y_axis else "") + xaxis)

    # --- X축 라벨 ---
    if x_labels and len(x_labels) == n:
        lab_row = [" " for _ in range(width)]
        for i, lab in enumerate(x_labels):
            s = str(lab); pos = i * x_step
            start = max(0, pos - (len(s)//2))
            for j, ch in enumerate(s):
                if 0 <= start+j < width:
                    lab_row[start+j] = ch
        lines.append(("       " if show_y_axis else "") + "".join(lab_row))

    # --- 범례 ---
    legend = " | ".join(f"{point_glyphs[i%len(point_glyphs)]} {keys[i]}" for i in range(len(keys)))
    lines.append(legend)

    # --- 시리즈 범위 표시 ---
    if show_series_ranges:
        if scale == "per_series":
            ranges = " | ".join(f"{k}: [{min(series_dict[k])}, {max(series_dict[k])}]" for k in keys)
            lines.append("ranges: " + ranges)
        elif scale in ("linear","robust"):
            lines.append(y_axis_note)
    else:
        lines.append(y_axis_note)

    # --- 실제 값 주석 처리 ---
    ann_lines = []
    idxs = []
    if annotate_last:
        idxs.append(n-1)  # 마지막 시점
    if annotate_indices:
        for ii in annotate_indices:
            if isinstance(ii, int):
                if ii < 0: ii = n + ii
                if 0 <= ii < n and ii not in idxs:
                    idxs.append(ii)
    idxs.sort()

    if idxs:
        for ii in idxs:
            parts = []
            for si, k in enumerate(keys):
                _, vals = series_points[k]
                parts.append(f"{k}={vals[ii]}")
            label = x_labels[ii] if x_labels and len(x_labels)==n else ii
            ann_lines.append(f"@{label}: " + " | ".join(parts))
    lines.extend(ann_lines)

    return "\n".join(lines)
