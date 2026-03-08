"""
build.py — AP.Econ.Graphs
==========================
Scans all .yaml files in the graphs/ folder, parses their front-matter,
and generates a structured content.json for the index page.

Usage:
    python build.py

Run from the AP Micro Graphs/ directory:

    AP Micro Graphs/
        build.py          ← run from here
        content.json      ← generated output
        graphs/
            6.2.G1.yaml
            6.2.G2.yaml
            ...

Workflow for adding a new graph:
    1. Create a new .yaml file in graphs/ with front-matter
    2. Run: python build.py
    3. content.json updates automatically — nothing else to touch
"""

import os
import json
import re


# ── UNIT LOOKUP TABLE ─────────────────────────────────────────────────────────
# Add a new entry here when you add a new unit.

UNITS = {
    '1': ('Unit 1 — Basic Economic Concepts',
          '第一单元 — 基本经济学概念'),
    '2': ('Unit 2 — Supply and Demand',
          '第二单元 — 供求关系'),
    '3': ('Unit 3 — Production, Cost, and the Perfect Competition Model',
          '第三单元 — 生产、成本与完全竞争模型'),
    '4': ('Unit 4 — Imperfect Competition',
          '第四单元 — 不完全竞争'),
    '5': ('Unit 5 — Factor Markets',
          '第五单元 — 要素市场'),
    '6': ('Unit 6 — Market Failure and the Role of Government',
          '第六单元 — 市场失灵与政府治理'),
}


# ── CHAPTER LOOKUP TABLE ──────────────────────────────────────────────────────
# Key: chapter code (e.g. '6.2')
# Value: (english title, chinese title)
# Add a new entry here when you add a new chapter.

CHAPTERS = {
    '1.1': ('Scarcity',
            '稀缺性'),
    '1.2': ('Resource Allocation and Economic Systems',
            '资源配置与经济体制'),
    '1.3': ('Production Possibilities Curve',
            '生产可能性曲线'),
    '1.4': ('Comparative Advantage and Trade',
            '比较优势与贸易'),
    '2.1': ('Demand',
            '需求'),
    '2.2': ('Supply',
            '供给'),
    '2.3': ('Price Elasticity of Demand',
            '需求价格弹性'),
    '2.4': ('Price Elasticity of Supply',
            '供给价格弹性'),
    '2.5': ('Other Elasticities',
            '其他弹性'),
    '2.6': ('Market Equilibrium, Disequilibrium, and Changes in Equilibrium',
            '市场均衡、非均衡与均衡变动'),
    '2.7': ('The Effects of Government Intervention in Markets',
            '政府干预市场的效应'),
    '2.8': ('International Trade and Public Policy',
            '国际贸易与公共政策'),
    '3.1': ('Types of Profit',
            '利润的类型'),            
    '3.2': ('The Production Function',
            '生产函数'),
    '3.3': ('Short-Run Production Costs',
            '短期生产成本'),
    '3.4': ('Perfect Competition',
            '完全竞争'),
    '4.1': ('Monopoly',
            '垄断'),
    '4.3': ('Price Discrimination',
            '价格歧视'),
    '4.4': ('Monopolistic Competition',
            '垄断竞争'),
    '4.5': ('Oligopoly and Game Theory',
            '寡头垄断与博弈论'),
    '5.1': ('Introduction to Factor Markets',
            '要素市场导论'),
    '5.2': ('Changes in Factor Demand and Factor Supply',
            '要素需求与供给的变动'),
    '5.3': ('Profit-Maximizing Behavior in Perfectly Competitive Factor Markets',
            '完全竞争要素市场的利润最大化'),
    '5.4': ('Monopsony',
            '买方垄断'),
    '5.5': ('Least-Cost Combination of Resources',
            '最低成本资源组合'),
    '6.1': ('Socially Efficient and Inefficient Market Outcomes',
            '社会有效与无效的市场结果'),
    '6.2': ('Externalities',
            '外部性'),
    '6.3': ('Public and Private Goods',
            '公共品与私人品'),
    '6.4': ('The Effects of Government Intervention in Different Market Structures',
            '政府干预在不同市场结构中的效应'),
}


# ── FRONT-MATTER PARSER ───────────────────────────────────────────────────────

def parse_front_matter(text):
    """
    Extract front-matter fields from a YAML file.
    Reads fields at the top of the file before the first 'schema:' line.
    Supports both single-line values and block scalars (|).
    """
    fields = {
        'title':       '',
        'title_zh':    '',
        'label':       '',
        'eyebrow':     '',
        'eyebrow_zh':  '',
        'description': '',
        'description_zh': '',
    }

    lines = text.split('\n')
    i = 0
    block_key = None
    block_lines = []

    def flush_block():
        nonlocal block_key, block_lines
        if block_key:
            fields[block_key] = '\n'.join(block_lines).strip()
            block_key = None
            block_lines = []

    while i < len(lines):
        line = lines[i]

        # Stop at schema definition
        if re.match(r'^schema:', line):
            flush_block()
            break

        # Collect block scalar lines
        if block_key is not None:
            if line.startswith('  ') or line.strip() == '':
                block_lines.append(line.strip())
                i += 1
            else:
                flush_block()
                continue
        else:
            m = re.match(r'^([a-zA-Z_]+):\s*(.*)', line)
            if m:
                key, val = m.group(1), m.group(2).strip()
                if key in fields:
                    if val in ('|', '>'):
                        block_key = key
                        block_lines = []
                    else:
                        fields[key] = val.strip('"\'')
            i += 1

    flush_block()
    return fields


# ── LABEL PARSER ──────────────────────────────────────────────────────────────

def parse_label(label):
    """
    Parse '6.2.G4' into:
        unit_num     = '6'
        chapter_code = '6.2'
    Returns (None, None) if label doesn't match expected format.
    """
    m = re.match(r'^(\d+)\.(\d+)\.G\d+$', label)
    if not m:
        return None, None
    unit_num     = m.group(1)
    chapter_code = f'{m.group(1)}.{m.group(2)}'
    return unit_num, chapter_code


# ── SORT KEY ──────────────────────────────────────────────────────────────────

def label_sort_key(label):
    """Numeric sort for labels like '6.2.G4' → (6, 2, 4)"""
    m = re.match(r'^(\d+)\.(\d+)\.G(\d+)$', label)
    if m:
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return (999, 999, 999)


# ── MAIN BUILD ────────────────────────────────────────────────────────────────

def build(graphs_dir='graphs', output_file='content.json'):

    # Verify graphs/ folder exists
    if not os.path.isdir(graphs_dir):
        print('❌  graphs/ folder not found.')
        print('    Make sure you run this script from inside AP Micro Graphs/')
        return

    # Collect all yaml files
    yaml_files = sorted([
        f for f in os.listdir(graphs_dir)
        if f.lower().endswith('.yaml') or f.lower().endswith('.yml')
    ])

    if not yaml_files:
        print('⚠️  No YAML files found in graphs/.')
        return

    # Parse each file
    parsed = []
    skipped = []

    for filename in yaml_files:
        filepath = os.path.join(graphs_dir, filename)
        with open(filepath, encoding='utf-8') as f:
            text = f.read()

        meta  = parse_front_matter(text)
        label = meta['label'].strip()

        # Fall back to filename if no label field
        if not label:
            label = re.sub(r'\.(yaml|yml)$', '', filename, flags=re.IGNORECASE)

        unit_num, chapter_code = parse_label(label)

        if not unit_num:
            print(f'⚠️  Skipping {filename} — label "{label}" not in format X.Y.GZ')
            skipped.append(filename)
            continue

        # Rename file to match its label (e.g. "My Graph.yaml" → "6.2.G1.yaml")
        new_filename = label + '.yaml'
        new_path = os.path.join(graphs_dir, new_filename)
        if os.path.abspath(filepath) != os.path.abspath(new_path):
            if not os.path.exists(new_path):
                os.rename(filepath, new_path)
                print(f'  Renamed: {filename} → {new_filename}')
            else:
                print(f'  ⚠️  Skipped rename: {new_filename} already exists')

        parsed.append({
            'id':          label,
            'title':       meta['title']    or label,
            'title_zh':    meta['title_zh'] or '',
            'unit':        unit_num,
            'chapter':     chapter_code,
        })

    if not parsed:
        print('❌  No valid graphs found. Check your YAML files have a label field.')
        return

    # Sort graphs by label numerically
    parsed.sort(key=lambda g: label_sort_key(g['id']))

    # Group: unit → chapter → graphs
    units_dict = {}

    for g in parsed:
        u = g['unit']
        c = g['chapter']

        if u not in units_dict:
            u_title, u_title_zh = UNITS.get(u, (f'Unit {u}', f'第{u}单元'))
            units_dict[u] = {
                'number':   f'Unit {u}',
                'title':    u_title,
                'title_zh': u_title_zh,
                'chapters': {}
            }

        if c not in units_dict[u]['chapters']:
            c_title, c_title_zh = CHAPTERS.get(c, (c, c))
            units_dict[u]['chapters'][c] = {
                'code':     c,
                'title':    c_title,
                'title_zh': c_title_zh,
                'graphs':   []
            }

        units_dict[u]['chapters'][c]['graphs'].append({
            'id':       g['id'],
            'title':    g['title'],
            'title_zh': g['title_zh'],
        })

    # Convert to sorted lists
    output = {'units': []}

    for u_key in sorted(units_dict.keys(), key=int):
        u = units_dict[u_key]
        chapters_list = [
            u['chapters'][c_key]
            for c_key in sorted(
                u['chapters'].keys(),
                key=lambda x: (int(x.split('.')[0]), int(x.split('.')[1]))
            )
        ]
        output['units'].append({
            'number':   u['number'],
            'title':    u['title'],
            'title_zh': u['title_zh'],
            'chapters': chapters_list,
        })

    # Write content.json
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # Summary
    total_units    = len(output['units'])
    total_chapters = sum(len(u['chapters']) for u in output['units'])
    total_graphs   = len(parsed)

    print(f'✅  content.json generated.')
    print(f'    {total_units} unit(s) · {total_chapters} chapter(s) · {total_graphs} graph(s)')
    if skipped:
        print(f'⚠️  Skipped {len(skipped)} file(s): {", ".join(skipped)}')


if __name__ == '__main__':
    build()