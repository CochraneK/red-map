#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build data/long_march_events.json from data_edit CSV tables.

人工维护建议：
- events.csv 可以用 Excel 编辑；date 支持 YYYYMMDD 或 YYYY-MM-DD；输出 JSON 统一为 YYYY-MM-DD。
- metrics/poem 等扩展字段可为空。
"""
from __future__ import annotations
import argparse, csv, json, re, sys
from datetime import date
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
EDIT_DIR = ROOT / 'data_edit'
DEFAULT_OUT = ROOT / 'data' / 'long_march_events.json'
TRUE_VALUES = {'1','true','yes','y','是','启用','include','included','保留'}
FALSE_VALUES = {'0','false','no','n','否','禁用','exclude','excluded','删除'}

def read_csv(name: str) -> list[dict[str,str]]:
    path = EDIT_DIR / name
    if not path.exists(): raise FileNotFoundError(f'缺少表格：{path}')
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        rows=[]
        for row_no,row in enumerate(csv.DictReader(f), start=2):
            if None in row and row[None]:
                extra='; '.join(str(v).strip() for v in row[None] if str(v).strip())
                raise ValueError(f'{name} 第 {row_no} 行列数超出表头：{extra}')
            rows.append({(k or '').strip():(v or '').strip() for k,v in row.items() if k is not None})
        return rows

def read_optional_csv(name: str) -> list[dict[str,str]]:
    path = EDIT_DIR / name
    if not path.exists(): return []
    return read_csv(name)

def split_cell(value: str) -> list[str]:
    return [p.strip() for p in re.split(r'[;；,，|｜]+', value or '') if p.strip()]

def is_enabled(value: str) -> bool:
    v = (value or '').strip().lower()
    if not v: return True
    if v in TRUE_VALUES: return True
    if v in FALSE_VALUES: return False
    return True

def parse_int(value: str, default=None, field='整数'):
    if value in ('', None): return default
    try: return int(float(str(value).strip()))
    except Exception: raise ValueError(f'{field} 不是有效整数：{value}')

def parse_float(value: str, field='数字') -> float:
    try: return float(str(value).strip())
    except Exception: raise ValueError(f'{field} 不是有效数字：{value}')

def normalize_date(value: str) -> str:
    raw = (value or '').strip()
    digits = re.sub(r'\D', '', raw)
    if len(digits) == 8:
        y, m, d = int(digits[:4]), int(digits[4:6]), int(digits[6:8])
    else:
        mobj = re.match(r'^(\d{4})-(\d{1,2})-(\d{1,2})$', raw)
        if not mobj: raise ValueError(f'date 必须是 YYYYMMDD 或 YYYY-MM-DD：{value}')
        y, m, d = map(int, mobj.groups())
    try: return date(y,m,d).isoformat()
    except Exception: raise ValueError(f'date 不是有效日期：{value}')

def make_id(row: dict[str,str], row_no: int) -> str:
    raw_date = re.sub(r'\D','', row.get('date','')) or 'date'
    force = re.sub(r'[^A-Za-z0-9_]+','_', row.get('forceId','force'))[:32]
    seq = re.sub(r'[^A-Za-z0-9_]+','_', row.get('sequence','') or f'{row_no:03d}')
    return f'evt_{raw_date}_{force}_{seq}'

def read_metadata() -> dict:
    kv = {r.get('key',''): r.get('value','') for r in read_csv('metadata.csv') if r.get('key')}
    return {'title': kv.get('title','红军长征路线动态地图'), 'description': kv.get('description',''), 'version': kv.get('version','table-generated'), 'timeRange': {'start': normalize_date(kv.get('timeRange.start','19341010')), 'end': normalize_date(kv.get('timeRange.end','19361022'))}}

def add_optional(obj: dict, row: dict, *fields):
    for f in fields:
        if row.get(f,'').strip(): obj[f] = row[f].strip()

def read_subjects(errors, warnings):
    subjects=[]; subject_ids=set(); force_ids=set()
    for i,row in enumerate(read_csv('subjects.csv'), start=2):
        if not any(row.values()): continue
        sid = row.get('id','').strip()
        if not sid: warnings.append(f'subjects.csv 第 {i} 行缺少 id，已跳过'); continue
        if sid in subject_ids: errors.append(f'subjects.csv 第 {i} 行 id 重复：{sid}'); continue
        subject_ids.add(sid)
        stype = row.get('type','force') or 'force'
        if stype == 'force': force_ids.add(sid)
        s = {'id': sid, 'type': stype, 'name': row.get('name',''), 'shortName': row.get('shortName',''), 'color': row.get('color','#777777') or '#777777', 'leader': row.get('leader',''), 'sort': parse_int(row.get('sort',''), 999, 'subjects.sort'), 'description': row.get('description','')}
        add_optional(s,row,'nameEn','shortNameEn','leaderEn','descriptionEn','subUnits','subUnitsEn')
        if row.get('isEnemy','').strip(): s['isEnemy'] = row.get('isEnemy','').strip().lower() in TRUE_VALUES
        subjects.append(s)
    return subjects, force_ids

def read_sources(errors, warnings):
    sources=[]; ids=set()
    for i,row in enumerate(read_csv('sources.csv'), start=2):
        if not any(row.values()): continue
        sid=row.get('id','').strip()
        if not sid: warnings.append(f'sources.csv 第 {i} 行缺少 id，已跳过'); continue
        if sid in ids: errors.append(f'sources.csv 第 {i} 行 id 重复：{sid}'); continue
        ids.add(sid)
        sources.append({'id':sid,'title':row.get('title',''),'publisher':row.get('publisher',''),'url':row.get('url',''),'note':row.get('note','')})
    return sources, ids

def check_refs(kind: str, row_no: int, field: str, values: list[str], allowed: set[str], errors: list[str]):
    missing = [v for v in values if v and v not in allowed]
    if missing: errors.append(f'{kind} 第 {row_no} 行 {field} 未定义：{"; ".join(missing)}')

def read_persons(errors, warnings, force_ids, source_ids):
    persons=[]; ids=set()
    for i,row in enumerate(read_optional_csv('persons.csv'), start=2):
        if not any(row.values()) or not is_enabled(row.get('enabled','TRUE')): continue
        pid=row.get('id','').strip()
        if not pid: warnings.append(f'persons.csv 第 {i} 行缺少 id，已跳过'); continue
        if pid in ids: errors.append(f'persons.csv 第 {i} 行 id 重复：{pid}'); continue
        ids.add(pid)
        force_id=row.get('forceId','').strip()
        if force_id: check_refs('persons.csv', i, 'forceId', [force_id], force_ids, errors)
        srcs=split_cell(row.get('sourceIds',''))
        check_refs('persons.csv', i, 'sourceIds', srcs, source_ids, errors)
        p={'id':pid,'name':row.get('name',''),'nameEn':row.get('nameEn',''),'personType':row.get('personType','人物') or '人物',
           'birthDate':row.get('birthDate',''),'deathDate':row.get('deathDate',''),'hometown':row.get('hometown',''),
           'hometownEn':row.get('hometownEn',''),'forceId':force_id,'summary':row.get('summary',''),'summaryEn':row.get('summaryEn',''),
           'portrait':row.get('portrait',''),'themeTags':split_cell(row.get('themeTags','')),'sourceIds':srcs,
           'certainty':row.get('certainty','medium') or 'medium','sort':parse_int(row.get('sort',''),999,'persons.sort')}
        persons.append(p)
    return sorted(persons,key=lambda p:(int(p.get('sort') or 999),p.get('id',''))), ids

def read_person_events(errors, warnings, person_ids, event_ids, source_ids):
    rows=[]
    for i,row in enumerate(read_optional_csv('person_events.csv'), start=2):
        if not any(row.values()) or not is_enabled(row.get('enabled','TRUE')): continue
        person_id=row.get('personId','').strip(); event_id=row.get('eventId','').strip()
        if not person_id or not event_id:
            warnings.append(f'person_events.csv 第 {i} 行缺少 personId 或 eventId，已跳过'); continue
        check_refs('person_events.csv', i, 'personId', [person_id], person_ids, errors)
        check_refs('person_events.csv', i, 'eventId', [event_id], event_ids, errors)
        srcs=split_cell(row.get('sourceIds',''))
        check_refs('person_events.csv', i, 'sourceIds', srcs, source_ids, errors)
        rows.append({'personId':person_id,'eventId':event_id,'role':row.get('role',''),'note':row.get('note',''),
                     'sourceIds':srcs,'sort':parse_int(row.get('sort',''),999,'person_events.sort')})
    return sorted(rows,key=lambda r:(r['personId'], int(r.get('sort') or 999), r['eventId']))

def read_museum_halls(errors, warnings):
    halls=[]; ids=set()
    for i,row in enumerate(read_optional_csv('museum_halls.csv'), start=2):
        if not any(row.values()) or not is_enabled(row.get('enabled','TRUE')): continue
        hid=row.get('id','').strip()
        if not hid: warnings.append(f'museum_halls.csv 第 {i} 行缺少 id，已跳过'); continue
        if hid in ids: errors.append(f'museum_halls.csv 第 {i} 行 id 重复：{hid}'); continue
        ids.add(hid)
        halls.append({'id':hid,'title':row.get('title',''),'titleEn':row.get('titleEn',''),'subtitle':row.get('subtitle',''),
                      'description':row.get('description',''),'theme':row.get('theme',''),'sort':parse_int(row.get('sort',''),999,'museum_halls.sort'),
                      'primaryExhibitId':row.get('primaryExhibitId','')})
    return sorted(halls,key=lambda h:(int(h.get('sort') or 999),h.get('id',''))), ids

def read_exhibits(errors, warnings, hall_ids, event_ids, person_ids, source_ids):
    exhibits=[]; ids=set()
    for i,row in enumerate(read_optional_csv('exhibits.csv'), start=2):
        if not any(row.values()) or not is_enabled(row.get('enabled','TRUE')): continue
        eid=row.get('id','').strip()
        if not eid: warnings.append(f'exhibits.csv 第 {i} 行缺少 id，已跳过'); continue
        if eid in ids: errors.append(f'exhibits.csv 第 {i} 行 id 重复：{eid}'); continue
        ids.add(eid)
        hall_id=row.get('hallId','').strip()
        check_refs('exhibits.csv', i, 'hallId', [hall_id], hall_ids, errors)
        related_events=split_cell(row.get('relatedEventIds',''))
        related_persons=split_cell(row.get('relatedPersonIds',''))
        srcs=split_cell(row.get('sourceIds',''))
        check_refs('exhibits.csv', i, 'relatedEventIds', related_events, event_ids, errors)
        check_refs('exhibits.csv', i, 'relatedPersonIds', related_persons, person_ids, errors)
        check_refs('exhibits.csv', i, 'sourceIds', srcs, source_ids, errors)
        exhibits.append({'id':eid,'hallId':hall_id,'title':row.get('title',''),'titleEn':row.get('titleEn',''),'type':row.get('type',''),
                         'summary':row.get('summary',''),'summaryEn':row.get('summaryEn',''),'relatedEventIds':related_events,
                         'relatedPersonIds':related_persons,'actionLabel':row.get('actionLabel',''),'actionHref':row.get('actionHref',''),
                         'sort':parse_int(row.get('sort',''),999,'exhibits.sort'),'sourceIds':srcs})
    return sorted(exhibits,key=lambda e:(e['hallId'], int(e.get('sort') or 999), e.get('id',''))), ids

def read_artifacts(errors, warnings, hall_ids, event_ids, person_ids, source_ids):
    artifacts=[]; ids=set()
    for i,row in enumerate(read_optional_csv('artifacts.csv'), start=2):
        if not any(row.values()) or not is_enabled(row.get('enabled','TRUE')): continue
        aid=row.get('id','').strip()
        if not aid: warnings.append(f'artifacts.csv 第 {i} 行缺少 id，已跳过'); continue
        if aid in ids: errors.append(f'artifacts.csv 第 {i} 行 id 重复：{aid}'); continue
        ids.add(aid)
        hall_id=row.get('hallId','').strip()
        related_events=split_cell(row.get('relatedEventIds',''))
        related_persons=split_cell(row.get('relatedPersonIds',''))
        srcs=split_cell(row.get('sourceIds',''))
        check_refs('artifacts.csv', i, 'hallId', [hall_id], hall_ids, errors)
        check_refs('artifacts.csv', i, 'relatedEventIds', related_events, event_ids, errors)
        check_refs('artifacts.csv', i, 'relatedPersonIds', related_persons, person_ids, errors)
        check_refs('artifacts.csv', i, 'sourceIds', srcs, source_ids, errors)
        artifacts.append({'id':aid,'hallId':hall_id,'title':row.get('title',''),'titleEn':row.get('titleEn',''),
                          'artifactType':row.get('artifactType',''),'summary':row.get('summary',''),'summaryEn':row.get('summaryEn',''),
                          'relatedPersonIds':related_persons,'relatedEventIds':related_events,'sourceIds':srcs,
                          'certainty':row.get('certainty','medium') or 'medium','sort':parse_int(row.get('sort',''),999,'artifacts.sort')})
    return sorted(artifacts,key=lambda a:(a['hallId'], int(a.get('sort') or 999), a.get('id',''))), ids

def read_visual_assets(errors, warnings, hall_ids, exhibit_ids, event_ids, person_ids, artifact_ids):
    assets=[]; ids=set()
    target_sets={'hero': {'museum'}, 'hall': hall_ids, 'exhibit': exhibit_ids, 'event': event_ids, 'person': person_ids, 'artifact': artifact_ids}
    for i,row in enumerate(read_optional_csv('visual_assets.csv'), start=2):
        if not any(row.values()) or not is_enabled(row.get('enabled','TRUE')): continue
        aid=row.get('id','').strip()
        if not aid: warnings.append(f'visual_assets.csv 第 {i} 行缺少 id，已跳过'); continue
        if aid in ids: errors.append(f'visual_assets.csv 第 {i} 行 id 重复：{aid}'); continue
        ids.add(aid)
        target_type=row.get('targetType','').strip()
        target_id=row.get('targetId','').strip()
        if target_type not in target_sets:
            errors.append(f'visual_assets.csv 第 {i} 行 targetType 不支持：{target_type}')
        else:
            check_refs('visual_assets.csv', i, 'targetId', [target_id], target_sets[target_type], errors)
        if not row.get('imageUrl','').strip():
            errors.append(f'visual_assets.csv 第 {i} 行 imageUrl 不能为空')
        assets.append({'id':aid,'targetType':target_type,'targetId':target_id,'title':row.get('title',''),'alt':row.get('alt',''),
                       'imageUrl':row.get('imageUrl',''),'imagePageUrl':row.get('imagePageUrl',''),'credit':row.get('credit',''),
                       'license':row.get('license',''),'sort':parse_int(row.get('sort',''),999,'visual_assets.sort')})
    return sorted(assets,key=lambda a:(a['targetType'], a['targetId'], int(a.get('sort') or 999), a.get('id','')))

def build(strict=True):
    errors=[]; warnings=[]
    metadata = read_metadata()
    subjects, force_ids = read_subjects(errors, warnings)
    sources, source_ids = read_sources(errors, warnings)
    events=[]; event_ids=set(); dedup=set()
    for i,row in enumerate(read_csv('events.csv'), start=2):
        if not any(row.values()) or not is_enabled(row.get('enabled','TRUE')): continue
        title=row.get('title','').strip()
        if not title: warnings.append(f'events.csv 第 {i} 行缺少 title，已跳过'); continue
        try:
            event_date=normalize_date(row.get('date',''))
            force_id=row.get('forceId','').strip()
            if force_id not in force_ids: raise ValueError(f'forceId 不存在于 subjects.csv 的 force 类型中：{force_id}')
            loc=row.get('locationName','').strip()
            if not loc: raise ValueError('locationName 不能为空')
            lat=parse_float(row.get('lat',''),'lat'); lng=parse_float(row.get('lng',''),'lng')
            if not (-90<=lat<=90 and -180<=lng<=180): raise ValueError(f'经纬度超出范围：lat={lat}, lng={lng}')
            importance=max(1,min(5,parse_int(row.get('importance',''),3,'importance') or 3))
            seq=parse_int(row.get('sequence',''), i, 'sequence') or i
        except Exception as exc:
            errors.append(f'events.csv 第 {i} 行错误：{exc}'); continue
        eid=row.get('id','').strip() or make_id(row,i)
        if eid in event_ids: errors.append(f'events.csv 第 {i} 行 id 重复：{eid}'); continue
        event_ids.add(eid)
        dkey=f'{event_date}|{force_id}|{title}|{loc}'
        if dkey in dedup: warnings.append(f'events.csv 第 {i} 行疑似重复事件，已跳过：{dkey}'); continue
        dedup.add(dkey)
        srcs=split_cell(row.get('sourceIds',''))
        missing=[sid for sid in srcs if sid not in source_ids]
        if missing: errors.append(f'events.csv 第 {i} 行 sourceIds 未定义：{"; ".join(missing)}'); continue
        ev={'id':eid,'date':event_date,'displayDate':event_date,'sequence':seq,'forceId':force_id,'type':row.get('type','其他') or '其他','title':title,'description':row.get('description',''),'location':{'name':loc,'coordinates':[lat,lng]},'participants':split_cell(row.get('participants','')),'importance':importance,'sourceIds':srcs,'certainty':row.get('certainty','medium') or 'medium'}
        add_optional(ev,row,'notes','titleEn','descriptionEn','result','casualties')
        if row.get('locationNameEn','').strip(): ev['location']['nameEn']=row['locationNameEn'].strip()
        metrics={}
        for col,key in [('redJoined','redJoined'),('redLosses','redLosses'),('enemyDefeated','enemyDefeated'),('distanceLi','distanceLi'),('victory','victory')]:
            val=row.get(col,'').strip()
            if not val: continue
            if key == 'victory': metrics[key]=val.lower() in TRUE_VALUES
            else: metrics[key]=parse_int(val,0,col)
        if metrics: ev['metrics']=metrics
        if row.get('poemLine','').strip(): ev['poem']={'line':row.get('poemLine','').strip(),'title':row.get('poemTitle','').strip(),'text':row.get('poemText','').strip()}
        events.append(ev)
    events.sort(key=lambda e:(e['date'], int(e.get('sequence') or 0), e['id']))
    persons, person_ids = read_persons(errors, warnings, force_ids, source_ids)
    person_events = read_person_events(errors, warnings, person_ids, event_ids, source_ids)
    museum_halls, hall_ids = read_museum_halls(errors, warnings)
    exhibits, exhibit_ids = read_exhibits(errors, warnings, hall_ids, event_ids, person_ids, source_ids)
    artifacts, artifact_ids = read_artifacts(errors, warnings, hall_ids, event_ids, person_ids, source_ids)
    visual_assets = read_visual_assets(errors, warnings, hall_ids, exhibit_ids, event_ids, person_ids, artifact_ids)
    for hid, primary in [(h.get('id',''), h.get('primaryExhibitId','')) for h in museum_halls if h.get('primaryExhibitId','')]:
        check_refs('museum_halls.csv', 0, f'primaryExhibitId for {hid}', [primary], exhibit_ids, errors)
    output={**metadata, 'sources':sources, 'subjects':sorted(subjects,key=lambda s:(int(s.get('sort') or 999),s.get('id',''))), 'events':events,
            'persons':persons, 'personEvents':person_events, 'museum': {'halls':museum_halls, 'exhibits':exhibits, 'artifacts':artifacts, 'visualAssets':visual_assets},
            'statsModel': {'startDate': metadata['timeRange']['start'], 'endDate': metadata['timeRange']['end'], 'centralDistanceLi':25000, 'overallParticipantsApprox':200000, 'overallLossesApprox':150000, 'survivorsApprox':'5–6万人', 'note':'动态统计采用史实口径与点位累积结合。'}}
    if strict and errors: raise ValueError('\n'.join(errors))
    return output, warnings, errors

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out', default=str(DEFAULT_OUT))
    parser.add_argument('--no-strict', action='store_true')
    args=parser.parse_args()
    try: data,warnings,errors=build(strict=not args.no_strict)
    except Exception as exc: print('[ERROR] 生成失败：', file=sys.stderr); print(exc, file=sys.stderr); return 1
    out=Path(args.out); out = out if out.is_absolute() else ROOT/out
    out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(data,ensure_ascii=False,indent=2), encoding='utf-8')
    print(f'[OK] 已生成：{out}')
    print(f"[OK] subjects={len(data['subjects'])}, sources={len(data['sources'])}, events={len(data['events'])}, persons={len(data.get('persons',[]))}, halls={len(data.get('museum',{}).get('halls',[]))}, visuals={len(data.get('museum',{}).get('visualAssets',[]))}")
    if warnings:
        print('\n[WARNINGS]'); [print('-',w) for w in warnings]
    if errors:
        print('\n[ERRORS - no-strict]'); [print('-',e) for e in errors]
    return 0
if __name__ == '__main__': raise SystemExit(main())


