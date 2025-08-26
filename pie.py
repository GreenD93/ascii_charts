def pie(
    labels, counts,
    radius=12,
    hole=0.0,
    start_at_12=True,
    clockwise=True,
    samples=4,
    y_scale=2.4,
    border="·",
    border_softness=0.45,
    chars=None,
    show_legend=True,
    label_mode="percent",
    label_max=4,
    title=None
):
    """
    Render a (roughly) circular pie or donut chart using ASCII characters.

    Parameters
    ----------
    labels : list[str]
        각 조각(웨지)의 라벨 목록.
    counts : list[int | float]
        각 라벨에 대응하는 값. labels와 길이가 같아야 함.
    radius : int, default=12
        차트의 반지름 (텍스트 격자 단위).
    hole : float, default=0.0
        도넛 모양의 구멍 비율. 0.0 → 파이, 0.99 → 얇은 링.
    start_at_12 : bool, default=True
        True이면 12시 방향부터 시작, False면 3시 방향부터 시작.
    clockwise : bool, default=True
        True이면 시계 방향으로, False이면 반시계 방향으로 진행.
    samples : int, default=4
        각 격자 셀 내부의 샘플링 횟수. 값이 클수록 외곽선이 매끄러움.
    y_scale : float, default=2.4
        세로 종횡비 보정 값. (문자가 세로로 길쭉한 경우 원형을 유지하기 위함)
    border : str, default="·"
        외곽/내곽 경계선에 사용할 문자. None 또는 ""로 두면 비활성화.
    border_softness : float, default=0.45
        경계 두께 민감도. 값이 클수록 경계선이 두꺼워짐.
    chars : list[str], optional
        웨지를 채우는 데 사용할 문자 집합. 제공하지 않으면 기본 팔레트 사용.
    show_legend : bool, default=True
        차트 하단에 범례(라벨, 값, 비율)를 표시할지 여부.
    label_mode : {"percent", "value", "both"}, default="percent"
        차트 내부에 배치되는 라벨 표시 방식.
    label_max : int, default=4
        내부에 표시할 라벨의 최대 개수. 큰 비율부터 우선.
    title : str, optional
        차트 상단에 표시할 제목.

    Returns
    -------
    str
        ASCII 문자열로 그려진 파이/도넛 차트.

    Notes
    -----
    - labels와 counts의 길이는 같아야 함.
    - counts 합계가 0 이하이면 "No data." 반환.
    - label_max를 초과하면 상위 항목만 표시됨.
    - title이 있으면 차트 위에 중앙 정렬된 제목이 출력됨.
    """
    
    import math

    # --- 입력 검증 ---
    if not labels or not counts or len(labels) != len(counts):
        return "Invalid input: labels and counts must be same-length non-empty lists."
    total = float(sum(counts))
    if total <= 0:
        return "No data."

    # --- 채움 문자 팔레트 설정 ---
    # 기본 팔레트는 시각적으로 구분이 잘 되는 블록 문자 위주
    default_chars = ["█", "░", "▒", "▓", "▩", "▦", "▧", "▨", "▤", "▥"]
    glyphs = (chars or default_chars)

    # --- 웨지(조각) 각도 빌드 ---
    # wedges: [label, angle_start, angle_end, fill_char, fraction, value]
    wedges = []
    cum = 0.0
    for i, (lab, val) in enumerate(zip(labels, counts)):
        frac = (val / total) if total else 0.0
        ang = 2 * math.pi * frac
        wedges.append([lab, cum, cum + ang, glyphs[i % len(glyphs)], frac, val])
        cum += ang

    # --- 각도 기준 변환 함수 ---
    # 기본 atan2는 3시(양의 x축)를 0으로 보고 반시계 방향이 양수.
    # 옵션에 따라 12시 시작/시계방향 진행으로 재해석.
    def orient(a):
        if a < 0: 
            a += 2 * math.pi
        if start_at_12: 
            a = (a - math.pi/2) % (2*math.pi)  # 12시를 0도로 맞춤
        if clockwise:   
            a = (-a) % (2*math.pi)             # 진행 방향 반전(시계방향)
        return a

    # 도넛 내부 반지름(입력 안정화: [0,0.99] 클램프)
    inner = max(0.0, min(0.99, float(hole))) * radius

    # --- 슈퍼샘플링 오프셋 준비 ---
    # 각 격자 셀을 내부에서 여러 지점 샘플링해 가장 많이 득표한 문자를 채택
    step = 1.0 / (samples + 1)
    offsets = [(k+1)*step - 0.5 for k in range(samples)]

    # --- 각도에 해당하는 웨지의 채움 문자를 찾기 ---
    def wedge_char(ang):
        for idx, (lab, a0, a1, ch, frac, val) in enumerate(wedges):
            last = (idx == len(wedges)-1)
            # 마지막 웨지는 끝각이 2π를 넘기며 0으로 래핑될 수 있으므로 별도 처리
            if a0 <= ang < a1 or (last and (ang >= a0 or ang < (a1 % (2*math.pi)))):
                return ch
        return " "  # 이론상 도달하지 않지만 안전망

    # --- 본 그리기 루프 ---
    lines = []
    for j in range(-radius, radius+1):
        row = []
        for i in range(-radius, radius+1):
            votes = {}       # 각 문자 득표수
            border_vote = 0  # 경계 후보 득표수
            inside = 0       # 샘플 중 원/도넛 영역에 속한 개수

            # 셀 내부 슈퍼샘플링
            for dy in offsets:
                for dx in offsets:
                    # 종횡비 보정: y를 y_scale로 나눠 원형에 가깝게
                    x, y = i+dx, (j+dy)/y_scale
                    r = math.hypot(x,y)

                    # (1) 외곽 반지름 밖이거나 (2) 도넛 내부(구멍)보다 작으면 비우기
                    if r > radius+1e-6 or r < inner-1e-6:
                        continue

                    inside += 1
                    ang = orient(math.atan2(y,x))
                    ch = wedge_char(ang)
                    votes[ch] = votes.get(ch,0)+1

                    # 경계 근처 샘플에 득표(외곽 또는 내곽 경계)
                    if border and (abs(r-radius)<border_softness or (inner>0 and abs(r-inner)<border_softness)):
                        border_vote += 1

            # 셀 최종 결정
            if inside == 0:
                row.append(" ")  # 완전히 빈 셀
            else:
                # 최다 득표 문자
                ch = max(votes.items(), key=lambda kv: kv[1])[0]
                # 경계 득표가 충분하면 경계 문자로 대체
                if border and border_vote > inside//3:
                    row.append(border)
                else:
                    row.append(ch)
        lines.append("".join(row))

    # --- 라벨 포맷터 ---
    def fmt(lbl, frac, val):
        if label_mode=="percent": return f"{lbl} {frac*100:.1f}%"
        if label_mode=="value":   return f"{lbl} {val}"
        if label_mode=="both":    return f"{lbl} {val} ({frac*100:.1f}%)"
        return f"{lbl} {frac*100:.1f}%"

    # --- 차트 내부(중앙 부근) 라벨 오버레이 ---
    # 상위 비율 label_max개를 뽑아 가운데 기준으로 위/아래 줄에 교차 배치
    if label_max and len(wedges)>0:
        ordered = sorted(wedges, key=lambda w:w[4], reverse=True)[:label_max]
        h=len(lines); mid=h//2; targets=[]

        # 라벨 배치 대상 줄(row)과 정렬방향(left/right) 결정
        for k in range(len(ordered)):
            # k: 0,1,2,3...
            offset=(k//2+1)*(2 if k>=2 else 1)  # 0,1은 1칸, 2,3은 2칸, 4,5는 3칸...
            row_idx=(mid-offset) if (k%2==0) else (mid+offset)
            align="left" if (k%2==0) else "right"
            row_idx=max(0,min(h-1,row_idx))
            targets.append((row_idx,align))

        # 실제 문자 덮어쓰기
        def place(row_idx,text,align="left"):
            row=list(lines[row_idx])

            # 현재 행에서 그려진 도형의 좌/우 끝 찾기
            first=next((k for k,c in enumerate(row) if c!=" "),None)
            last=len(row)-1-next((k for k,c in enumerate(reversed(row)) if c!=" "),0)

            if first is None or last<=first: 
                return  # 이 행은 비어있음(안전 탈출)

            span=last-first+1
            pad=1  # 양 끝 1칸 여백
            left_limit=first+pad
            right_limit=last-pad

            # 라벨 양쪽에 공백 1칸
            text=" "+text+" "

            # 공간이 모자라면 잘라냄(하드 클램프)
            if len(text)>(right_limit-left_limit+1):
                text=text[:max(0,right_limit-left_limit+1)]

            # 정렬에 따른 시작 위치
            if align=="left": 
                start=left_limit
            elif align=="right": 
                start=right_limit-len(text)+1
            else: 
                start=left_limit+( (right_limit-left_limit+1)-len(text))//2

            # 문자 덮어쓰기(경계를 침범하지 않도록 범위 체크)
            for idx,ch in enumerate(text):
                col=start+idx
                if 0<=col<len(row): 
                    row[col]=ch

            lines[row_idx]="".join(row)

        # 상위 항목들에 대해 순서대로 배치
        for (w,(row_idx,align)) in zip(ordered,targets):
            lbl,a0,a1,ch,frac,val=w
            place(row_idx,fmt(lbl,frac,val),align)

    # --- 범례 구성 ---
    legend_lines=[]
    if show_legend:
        # '문자 라벨 값 (비율%)' 형식으로 한 줄에 연결
        legend_parts=[f"{w[3]} {w[0]} {w[5]} ({w[4]*100:.1f}%)" for w in wedges]
        legend_lines.append(" | ".join(legend_parts))

    # --- 제목 및 최종 출력 조립 ---
    out=[]
    if title:
        # 제목 라인을 전체 폭보다 약간 넓게 깔끔하게 중앙 정렬
        out.append(title.center(radius*2+20,"="))
        out.append("")
    out.extend(lines)
    out.extend(legend_lines)

    return "\n".join(out)
