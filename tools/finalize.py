#!/usr/bin/env python3
"""data.json に overrides.csv(手直し)を当て、csv/stores.csv と csv/items.csv を書き出す。何度実行しても同じ結果になる。"""
import csv, json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data.json')
OVR = os.path.join(ROOT, 'overrides.csv')

def num(s):
    s = (s or '').strip().replace(',', '').replace('円', '')
    if s == '': return None
    return int(float(s)) if float(s).is_integer() else float(s)

def load_overrides():
    rows = []
    if not os.path.exists(OVR): return rows
    with open(OVR, encoding='utf-8-sig', newline='') as f:
        for r in csv.DictReader(f):
            if not (r.get('商品名') or '').strip(): continue
            if (r.get('郵便番号') or '').lstrip().startswith('#'): continue
            rows.append(r)
    return rows

def main():
    d = json.load(open(DATA, encoding='utf-8'))
    rows = load_overrides(); used = [0] * len(rows)
    for a in d['areas']:
        keep = []
        for it in a['items']:
            drop = False
            for n, r in enumerate(rows):
                if (r.get('商品名') or '').strip() != it['name']: continue
                if (r.get('店名') or '').strip() not in ('', it['store']): continue
                if (r.get('郵便番号') or '').strip() not in ('', a['zip']): continue
                used[n] += 1
                if (r.get('操作') or '').strip() == '削除': drop = True; break
                p = num(r.get('価格'))
                if p is not None: it['price'] = p; it['priceText'] = None
                if (r.get('価格表示') or '').strip(): it['priceText'] = r['価格表示'].strip(); it['price'] = None
                if (r.get('通常価格') or '').strip(): it['regular'] = num(r['通常価格'])
                if (r.get('メモ') or '').strip(): it['note'] = r['メモ'].strip()
            if not drop: keep.append(it)
        a['items'] = keep
    json.dump(d, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    os.makedirs(os.path.join(ROOT, 'csv'), exist_ok=True)
    with open(os.path.join(ROOT, 'csv', 'stores.csv'), 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f); w.writerow(['郵便番号', '地域', '店名', '距離km', '期間', '駐車場', '台数', '駐車場メモ', '緯度', '経度', 'チラシURL'])
        for a in d['areas']:
            for s in a['stores']:
                w.writerow([a['zip'], a.get('region', ''), s['name'], s.get('distanceKm'), s.get('period'), s.get('parking'), s.get('parkingSpaces'), s.get('parkingNote'), s.get('lat'), s.get('lng'), s.get('leafletUrl')])
    with open(os.path.join(ROOT, 'csv', 'items.csv'), 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f); w.writerow(['郵便番号', '店名', '分類', '商品名', '量', '価格', '価格表示', '通常価格', '期間', 'メモ'])
        for a in d['areas']:
            for i in a['items']:
                w.writerow([a['zip'], i['store'], i.get('category'), i['name'], i.get('unit'), i.get('price'), i.get('priceText'), i.get('regular'), i.get('period'), i.get('note')])
    for n, r in enumerate(rows):
        if not used[n]: print('当てはまる商品なし:', r.get('店名'), r.get('商品名'), file=sys.stderr)
    print('ok', sum(len(a['items']) for a in d['areas']), 'items', len(rows), 'overrides')

if __name__ == '__main__': main()
