#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import random
import sys
import os
import subprocess
import platform
import argparse
from typing import List
try:
    from rich.console import Console
    from rich.live import Live
    from rich.text import Text
except Exception:
    Console = None
    Live = None
    Text = None
try:
    import numpy as np
except Exception:
    np = None

# 터미널 색상 코드
class Colors:
    GREEN = '\033[92m'      # 밝은 초록색
    RED = '\033[91m'         # 밝은 빨강
    YELLOW = '\033[93m'      # 노랑
    CYAN = '\033[96m'        # 파랑
    WHITE = '\033[97m'       # 하양
    RESET = '\033[0m'        # 리셋
    BOLD = '\033[1m'         # 굵게
    
    @staticmethod
    def rgb(r: int, g: int, b: int) -> str:
        """RGB 색상 코드 생성"""
        return f'\033[38;2;{r};{g};{b}m'

def clear_screen():
    """터미널 화면 초기화"""
    sys.stdout.write('\033[2J\033[H')
    sys.stdout.flush()

def create_tree_structure(mode: str = 'double', density: float = 0.25, max_width: int = 50, gap: int = 1):
    """조명 위치를 미리 정한 크리스마스 트리 생성

    mode: 'single' (one big triangle) or 'double' (two stacked triangles)
    density: 전구 밀도 (0-1)
    max_width: 터미널 중앙 기준 너비
    """

    # 조명 색상
    light_colors = [
        Colors.RED,
        Colors.YELLOW,
        Colors.CYAN,
        Colors.WHITE,
        Colors.rgb(255, 192, 203),  # 분홍색
    ]

    # 트리 색상 팔레트
    colors = [Colors.GREEN, Colors.rgb(34, 139, 34), Colors.rgb(0, 100, 0)]

    tree_data = []

    # (no top banner by default)

    def make_triangle(base_width, height, color):
        for row in range(1, height + 1):
            # 비례적으로 너비 결정
            current_width = max(1, (base_width * row) // height)
            if current_width % 2 == 0:
                current_width -= 1
            padding = (max_width - current_width) // 2
            row_data = {'padding': padding, 'chars': []}
            for col in range(current_width):
                has_light = random.random() < density
                light_color = random.choice(light_colors) if has_light else None
                row_data['chars'].append({
                    'has_light': has_light,
                    'light_color': light_color,
                    'phase': random.randint(0, 3),
                    'tree_color': color
                })
            tree_data.append(row_data)
        # 빈 줄
        # tree_data.append({'padding': 0, 'chars': [], 'is_empty': True})

    if mode == 'single':
        # 한개의 큰 삼각형
        base = min(41, max_width - 2)
        height = 20
        make_triangle(base, height, colors[0])
    else:
        # 두 개의 삼각형 (작은 위쪽, 큰 아래쪽)
        top_base = min(21, max_width - 10)
        top_height = 10
        bottom_base = min(41, max_width - 2)
        bottom_height = 11
        make_triangle(top_base, top_height, colors[0])
        # # 중간 공백 추가 (gap 줄)
        # for _ in range(max(0, gap)):
        #     tree_data.append({'padding': 0, 'chars': [], 'is_empty': True})
        make_triangle(bottom_base, bottom_height, colors[1])

    # 트리 줄기
    trunk_width = max(1, base // 13) if mode == 'single' else 3
    trunk_padding = (max_width - trunk_width) // 2
    trunk_color = Colors.rgb(139, 69, 19)
    for _ in range(4):
        tree_data.append({'trunk': True, 'padding': trunk_padding, 'width': trunk_width, 'color': trunk_color})

    # 별
    star_padding = (max_width - 1) // 2
    tree_data.append({'star': True, 'padding': star_padding})

    return tree_data

def print_tree_with_lights(tree_data, animation_frame: int):
    """조명 위치가 고정된 크리스마스 트리 출력"""
    
    light_colors = [
        Colors.RED,
        Colors.YELLOW,
        Colors.CYAN,
        Colors.WHITE,
        Colors.rgb(255, 192, 203),  # 분홍색
    ]
    
    output = []
    
    for row_data in tree_data:
        # 배너(큰 별 등) 라인
        if row_data.get('banner'):
            output.append(row_data['text'])
            continue
        # 빈 줄
        if row_data.get('is_empty'):
            output.append('')
        # 줄기
        elif row_data.get('trunk'):
            line = ' ' * row_data['padding']
            if row_data.get('visible', True):
                line += row_data['color'] + '*' * row_data['width'] + Colors.RESET
            else:
                line += ' ' * row_data['width']
            output.append(line)
        # 별
        elif row_data.get('star'):
            line = ' ' * row_data['padding']
            if row_data.get('visible', True):
                line += Colors.YELLOW + '✨' + Colors.RESET
            else:
                line += ' '
            output.append(line)
        # 트리 줄
        else:
            line = ' ' * row_data['padding']
            
            for char_data in row_data['chars']:
                if not char_data.get('visible', True):
                    # 아직 빌드되지 않은 위치
                    line += ' '
                    continue

                if char_data['has_light']:
                    # 깜빡임 효과: per-light phase를 더해 불규칙하게 깜빡임
                    if (animation_frame + char_data.get('phase', 0)) % 4 < 2:
                        # 켜진 상태는 더 눈에 띄게 '●' 사용
                        line += char_data['light_color'] + '●' + Colors.RESET
                    else:
                        # 꺼진 상태는 어두운 초록색 '*' 사용
                        line += Colors.rgb(0, 80, 0) + '*' + Colors.RESET
                else:
                    # 일반 트리 별
                    line += char_data['tree_color'] + '*' + Colors.RESET
            
            output.append(line)
    
    return '\n'.join(output)

def render_tree_rich(tree_data, animation_frame: int):
    """Rich용 렌더러: ANSI 문자열을 Text로 변환해 반환"""
    ansi_str = print_tree_with_lights(tree_data, animation_frame)
    if Text is not None:
        return Text.from_ansi(ansi_str)
    # fallback
    return ansi_str

def render_full_rich(tree_data, animation_frame: int):
    """제목, 트리, 푸터를 합쳐서 하나의 Text로 반환"""
    title = f"{Colors.BOLD}{Colors.GREEN}🎄 Merry Christmas! 🎄{Colors.RESET}\n\n"
    footer = (f"{Colors.RED}{Colors.BOLD}✨ Jingle Bells! ✨{Colors.RESET}"
              if (animation_frame % 4) < 2
              else f"{Colors.YELLOW}{Colors.BOLD}⭐ Merry Christmas! ⭐{Colors.RESET}")

    ansi_str = title + print_tree_with_lights(tree_data, animation_frame) + "\n\n" + footer
    if Text is not None:
        return Text.from_ansi(ansi_str)
    return ansi_str

def animate_tree(duration: int = 60, mode: str = 'double', density: float = 0.25, speed: float = 0.5, max_width: int = 50, build: bool = False, build_speed: float = 0.02, auto_twinkle: bool = False, gap: int = 1, build_mode: str = 'sequential', seed: int | None = None, teardown: bool = False, teardown_speed: float = 0.02, teardown_mode: str = 'random'):
    """크리스마스 트리 애니메이션"""
    try:
        # 한 번만 트리 구조 생성
        tree_data = create_tree_structure(mode=mode, density=density, max_width=max_width, gap=gap)

        # 빌드 애니메이션을 위해 모든 요소의 visible 플래그 초기화
        for row in tree_data:
            if row.get('chars') is not None:
                for c in row['chars']:
                    c['visible'] = not build
            if row.get('trunk'):
                row['visible'] = not build
            if row.get('star'):
                row['visible'] = not build

        start_time = time.time()
        frame = 0
        # 음악 파일 경로 (하드코딩)
        MUSIC_PATH = '/Users/seungmin/Desktop/tree/Santa-/JINGLE_BELLS .mp3'
        music_proc = None
        # 자동 재생 (macOS에서는 afplay 사용)
        try:
            if os.path.exists(MUSIC_PATH):
                if platform.system() == 'Darwin':
                    music_proc = subprocess.Popen(['afplay', MUSIC_PATH])
                else:
                    # Linux/other: try ffplay
                    music_proc = subprocess.Popen(['ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet', MUSIC_PATH])
        except Exception as e:
            print(f"Warning: could not start music: {e}")

        # Rich가 설치되어 있으면 Live 업데이트로 한 번만 그린 뒤 내부만 업데이트
        if Console is not None and Live is not None and Text is not None:
            console = Console()
            # 초기 렌더
            with Live(render_full_rich(tree_data, 0), console=console, refresh_per_second=24) as live:
                # 빌드 애니메이션: 차례대로 visible 켜기
                if build:
                    char_positions = []
                    for r_idx, row in enumerate(tree_data):
                        if row.get('chars'):
                            for c_idx, _ in enumerate(row['chars']):
                                char_positions.append((r_idx, c_idx))

                    # shuffle character positions if requested
                    if build_mode == 'random':
                        if seed is not None:
                            random.seed(seed)
                            random.shuffle(char_positions)
                        elif np is not None:
                            char_positions = list(np.random.permutation(char_positions))
                        else:
                            random.shuffle(char_positions)

                    positions = [('char', r, c) for (r, c) in char_positions]

                    # append trunk and star last
                    for r_idx, row in enumerate(tree_data):
                        if row.get('trunk'):
                            positions.append(('trunk', r_idx))
                    for r_idx, row in enumerate(tree_data):
                        if row.get('star'):
                            positions.append(('star', r_idx))

                    for pos in positions:
                        if pos[0] == 'char':
                            _, r_idx, c_idx = pos
                            tree_data[r_idx]['chars'][c_idx]['visible'] = True
                        elif pos[0] == 'trunk':
                            _, r_idx = pos
                            tree_data[r_idx]['visible'] = True
                        elif pos[0] == 'star':
                            _, r_idx = pos
                            tree_data[r_idx]['visible'] = True

                        live.update(render_full_rich(tree_data, 0))
                        time.sleep(build_speed)
                # 빌드 이후에 자동으로 반짝일지 결정
                twinkle_enabled = (not build) or auto_twinkle

                while time.time() - start_time < duration:
                    # 깜빡임을 반영한 렌더 업데이트 (제목+트리+푸터를 한 번에 업데이트)
                    # 빌드가 완료되고 auto_twinkle이 False이면 고정된 프레임(0)을 사용
                    frame_for_render = frame if twinkle_enabled else 0
                    live.update(render_full_rich(tree_data, frame_for_render))

                    frame += 1
                    time.sleep(speed)

                # teardown phase: remove lights/trunk/star in order
                if teardown:
                    # collect all removable positions
                    positions = []
                    for r_idx, row in enumerate(tree_data):
                        if row.get('chars'):
                            for c_idx, _ in enumerate(row['chars']):
                                positions.append(('char', r_idx, c_idx))
                        if row.get('trunk'):
                            positions.append(('trunk', r_idx))
                        if row.get('star'):
                            positions.append(('star', r_idx))

                    if teardown_mode == 'random':
                        if seed is not None:
                            random.seed(seed)
                            random.shuffle(positions)
                        elif np is not None:
                            positions = list(np.random.permutation(positions))
                        else:
                            random.shuffle(positions)
                    else:
                        # reverse order: remove from bottom to top
                        positions = list(reversed(positions))

                    for pos in positions:
                        if pos[0] == 'char':
                            _, r_idx, c_idx = pos
                            tree_data[r_idx]['chars'][c_idx]['visible'] = False
                        elif pos[0] == 'trunk':
                            _, r_idx = pos
                            tree_data[r_idx]['visible'] = False
                        elif pos[0] == 'star':
                            _, r_idx = pos
                            tree_data[r_idx]['visible'] = False

                        live.update(render_full_rich(tree_data, 0))
                        time.sleep(teardown_speed)

                    # final message
                    msg = f"\n{Colors.BOLD}{Colors.GREEN}🎄 Happy Solo Christmas 🎄{Colors.RESET}\n"
                    if Text is not None:
                        live.update(Text.from_ansi(msg))
                    else:
                        live.update(msg)
                    time.sleep(2.0)
                    # stop music if playing
                    try:
                        if music_proc is not None and hasattr(music_proc, 'terminate'):
                            music_proc.terminate()
                            music_proc.wait(timeout=1)
                    except Exception:
                        pass
        else:
            # Rich가 없으면 기존 방식(fallback)
            # 빌드 애니메이션 (폴백)
            if build:
                char_positions = []
                for r_idx, row in enumerate(tree_data):
                    if row.get('chars'):
                        for c_idx, _ in enumerate(row['chars']):
                            char_positions.append((r_idx, c_idx))

                if build_mode == 'random':
                    if seed is not None:
                        random.seed(seed)
                        random.shuffle(char_positions)
                    elif np is not None:
                        char_positions = list(np.random.permutation(char_positions))
                    else:
                        random.shuffle(char_positions)

                positions = [('char', r, c) for (r, c) in char_positions]
                for r_idx, row in enumerate(tree_data):
                    if row.get('trunk'):
                        positions.append(('trunk', r_idx))
                for r_idx, row in enumerate(tree_data):
                    if row.get('star'):
                        positions.append(('star', r_idx))

                for pos in positions:
                    if pos[0] == 'char':
                        _, r_idx, c_idx = pos
                        tree_data[r_idx]['chars'][c_idx]['visible'] = True
                    elif pos[0] == 'trunk':
                        _, r_idx = pos
                        tree_data[r_idx]['visible'] = True
                    elif pos[0] == 'star':
                        _, r_idx = pos
                        tree_data[r_idx]['visible'] = True

                    clear_screen()
                    title = f"{Colors.BOLD}{Colors.GREEN}🎄 Merry Christmas! 🎄{Colors.RESET}"
                    print(title)
                    print()
                    print(print_tree_with_lights(tree_data, 0))
                    time.sleep(build_speed)

            # teardown phase (fallback)
            if teardown:
                positions = []
                for r_idx, row in enumerate(tree_data):
                    if row.get('chars'):
                        for c_idx, _ in enumerate(row['chars']):
                            positions.append(('char', r_idx, c_idx))
                    if row.get('trunk'):
                        positions.append(('trunk', r_idx))
                    if row.get('star'):
                        positions.append(('star', r_idx))

                if teardown_mode == 'random':
                    if seed is not None:
                        random.seed(seed)
                        random.shuffle(positions)
                    elif np is not None:
                        positions = list(np.random.permutation(positions))
                    else:
                        random.shuffle(positions)
                else:
                    positions = list(reversed(positions))

                for pos in positions:
                    if pos[0] == 'char':
                        _, r_idx, c_idx = pos
                        tree_data[r_idx]['chars'][c_idx]['visible'] = False
                    elif pos[0] == 'trunk':
                        _, r_idx = pos
                        tree_data[r_idx]['visible'] = False
                    elif pos[0] == 'star':
                        _, r_idx = pos
                        tree_data[r_idx]['visible'] = False

                    clear_screen()
                    title = f"{Colors.BOLD}{Colors.GREEN}🎄 Merry Christmas! 🎄{Colors.RESET}"
                    print(title)
                    print()
                    print(print_tree_with_lights(tree_data, 0))
                    time.sleep(teardown_speed)

                # final message (fallback)
                clear_screen()
                print(f"\n{Colors.BOLD}{Colors.GREEN}🎄 Happy Solo Christmas 🎄{Colors.RESET}\n")
                time.sleep(2.0)
                # stop music if playing
                try:
                    if music_proc is not None and hasattr(music_proc, 'terminate'):
                        music_proc.terminate()
                        music_proc.wait(timeout=1)
                except Exception:
                    pass

            twinkle_enabled = (not build) or auto_twinkle
            while time.time() - start_time < duration:
                clear_screen()

                # 제목 출력
                title = f"{Colors.BOLD}{Colors.GREEN}🎄 Merry Christmas! 🎄{Colors.RESET}"
                print(title)
                print()

                # 트리 출력 (조명만 깜빡임)
                frame_for_render = frame if twinkle_enabled else 0
                print(print_tree_with_lights(tree_data, frame_for_render))

                # 깜빡이는 텍스트 (애니메이션 효과)
                if frame % 4 < 2:
                    footer = f"{Colors.RED}{Colors.BOLD}✨ Jingle Bells! ✨{Colors.RESET}"
                else:
                    footer = f"{Colors.YELLOW}{Colors.BOLD}⭐ Merry Christmas! ⭐{Colors.RESET}"

                print(f"\n{footer}\n")

                frame += 1
                time.sleep(speed)  # 애니메이션 속도 조절

    except KeyboardInterrupt:
        clear_screen()
        print(f"{Colors.GREEN}{Colors.BOLD}🎄 Happy Holidays! 🎄{Colors.RESET}\n")
        sys.exit(0)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Terminal Christmas tree')
    parser.add_argument('--duration', type=int, default=60, help='애니메이션 지속 시간(초)')
    parser.add_argument('--mode', choices=['single', 'double'], default='double', help='트리 모드: single 또는 double')
    parser.add_argument('--density', type=float, default=0.25, help='조명 밀도 (0-1)')
    parser.add_argument('--speed', type=float, default=0.5, help='깜빡임 속도 (초)')
    parser.add_argument('--width', type=int, default=50, help='터미널 폭 기준(중앙 정렬용)')
    parser.add_argument('--build', action='store_true', help='빌드 애니메이션을 활성화')
    parser.add_argument('--build-speed', type=float, default=0.02, help='빌드 애니메이션 속도 (초)')
    parser.add_argument('--auto-twinkle', action='store_true', help='빌드 후 자동으로 조명이 반짝이게 함')
    parser.add_argument('--gap', type=int, default=1, help='두 삼각형 사이 공백 줄 수 (double 모드)')
    parser.add_argument('--teardown', action='store_true', help='애니메이션 종료 시 트리를 무작위로 사라지게 함')
    parser.add_argument('--teardown-speed', type=float, default=0.02, help='트리 사라짐 속도 (초)')
    parser.add_argument('--teardown-mode', choices=['random', 'reverse'], default='random', help='트리를 사라지게 하는 순서')
    parser.add_argument('--build-mode', choices=['sequential', 'random'], default='sequential', help='빌드 순서: sequential 또는 random')
    parser.add_argument('--seed', type=int, default=None, help='빌드 무작위 시드 (선택적)')
    args = parser.parse_args()

    animate_tree(duration=args.duration, mode=args.mode, density=args.density, speed=args.speed, max_width=args.width, build=args.build, build_speed=args.build_speed, auto_twinkle=args.auto_twinkle, gap=args.gap, build_mode=args.build_mode, seed=args.seed, teardown=args.teardown, teardown_speed=args.teardown_speed, teardown_mode=args.teardown_mode)
