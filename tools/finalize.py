#!/usr/bin/env python3
"""data.json に overrides.csv(手直し)を当て、csv/stores.csv と csv/items.csv を書き出す。何度実行しても同じ結果になる。
手直しは、チラシ側の価格か期間が変わったら自動で失効する(状態列に「期限切れ」と記録)。"""
import csv, datetime, json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data.json')
OVR = os.path.join(ROOT, 'overrides.csv')
COLS = ['郵便番号', '店名', '商品名', '価格', '価格表示', '通常価格', 'メモ', '操作', '元の価格', '元の期間', '状態']
TODAY = (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).strftime('%Y-%m-%d')

def num(s):
    s = (s or '').strip().replace(',', '').replace('円', '')
    if s == '': return None
    v = float(s); return int(v) if v.is_integer() else v

def raw_key(price, ptext):
    return '' if price is None and not ptext else (str(price) if price is not None else 'T:' + str(ptext))

def load_overrides():
    if not os.path.exists(OVR): return []
    with open(OVR, encoding='utf-8-sig', newline='') as f:
        return [{c: (r.get(c) or '') for c in COLS} for r in csv.DictReader(f)]

def is_row(r):
    return r['商品名'].strip() != '' and not r['郵便番号'].lstrip().startswith('#')

def main():
    d = json.load(open(DATA, encoding='utf-8'))
    rows = load_overrides(); seen = [0] * len(rows)
    for a in d['areas']:
        keep = []
        for it in a['items']:
            # 前回の手直しを外した「元の値」(data.json に手直し済みで残っている場合)
            raw = it.pop('_raw', None) or {'price': it.get('price'), 'priceText': it.get('priceText'), 'period': it.get('period'), 'regular': it.get('regular'), 'note': it.get('note')}
            for _k in ('price','priceText','period','regular','note'):
                if raw.get(_k) is None: it.pop(_k, None)
                else: it[_k] = raw[_k]
            drop = False
            for n, r in enumerate(rows):
                if not is_row(r) or r['商品名'].strip() != it['name']: continue
                if r['店名'].strip() not in ('', it['store']): continue
                if r['郵便番号'].strip() not in ('', a['zip']): continue
                seen[n] += 1
                if r['状態'].startswith('期限切れ'): continue
                cur_key, cur_period = raw_key(it.get('price'), it.get('priceText')), it.get('period') or ''
                if r['元の期間'] == '' and r['元の価格'] == '':
                    r['元の価格'], r['元の期間'] = cur_key, cur_period      # はじめて当てた時の元の値を記録
                elif r['元の価格'] != cur_key or r['元の期間'] != cur_period:
                    r['状態'] = '期限切れ(%s)' % TODAY                       # チラシ側が変わった → 自動失効
                    continue
                r['状態'] = '適用中'
                it['_raw'] = raw
                if r['操作'].strip() == '削除': drop = True; break
                p = num(r['価格'])
                if p is not None: it['price'] = p; it['priceText'] = None
                if r['価格表示'].strip(): it['priceText'] = r['価格表示'].strip(); it['price'] = None
                if r['通常価格'].strip(): it['regular'] = num(r['通常価格'])
                if r['メモ'].strip(): it['note'] = r['メモ'].strip()
            if not drop: keep.append(it)
            else: pass
        a['items'] = keep
    for n, r in enumerate(rows):
        if is_row(r) and not seen[n] and r['状態'] in ('', '適用中') and r['元の期間'] != '':
            # 削除済みの行は、削除した商品が data.json に残らないため「見つからない」になる → 再構築後に再確認される
            r['状態'] = r['状態'] or '該当なし'
    json.dump(d, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    with open(OVR, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=COLS); w.writeheader(); w.writerows(rows)
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
    print('ok', sum(len(a['items']) for a in d['areas']), 'items', sum(1 for r in rows if is_row(r)), 'overrides')

if __name__ == '__main__': main()
