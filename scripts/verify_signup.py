import os, json, urllib.request, urllib.error
PAT=os.environ['PAT']; REF=os.environ['REF']
SUPA=f'https://{REF}.supabase.co'; APP='https://wscc.vercel.app'
keys=json.load(urllib.request.urlopen(urllib.request.Request(
    f'https://api.supabase.com/v1/projects/{REF}/api-keys?reveal=true',
    headers={'Authorization':f'Bearer {PAT}'})))
ANON=next(k['api_key'] for k in keys if k['name']=='anon')
SVC=next(k['api_key'] for k in keys if k['name']=='service_role')
SVCH={'apikey':SVC,'Authorization':f'Bearer {SVC}','Content-Type':'application/json'}

def req(method,url,headers=None,body=None):
    r=urllib.request.Request(url,method=method,data=(json.dumps(body).encode() if body is not None else None),
        headers=headers or {})
    try:
        resp=urllib.request.urlopen(r); return resp.status, json.loads(resp.read() or b'{}')
    except urllib.error.HTTPError as e:
        try: return e.code, json.loads(e.read() or b'{}')
        except: return e.code, {}

def signup(email,pwd):
    s,d=req('POST',f'{SUPA}/auth/v1/signup',{'apikey':ANON,'Content-Type':'application/json'},{'email':email,'password':pwd})
    return d.get('access_token')
def token(email,pwd):
    s,d=req('POST',f'{SUPA}/auth/v1/token?grant_type=password',{'apikey':ANON,'Content-Type':'application/json'},{'email':email,'password':pwd})
    return d.get('access_token')
def admin_create(email,pwd):
    req('POST',f'{SUPA}/auth/v1/admin/users',SVCH,{'email':email,'password':pwd,'email_confirm':True})
def auth_delete(email):
    s,us=req('GET',f'{SUPA}/auth/v1/admin/users?per_page=200',SVCH)
    for u in us.get('users',[]):
        if (u.get('email') or '').lower()==email.lower():
            req('DELETE',f'{SUPA}/auth/v1/admin/users/{u["id"]}',SVCH)
def dbq(sql):
    req('POST',f'https://api.supabase.com/v1/projects/{REF}/database/query',
        {'Authorization':f'Bearer {PAT}','Content-Type':'application/json'},{'query':sql})
def apph(tok): return {'Authorization':f'Bearer {tok}','Content-Type':'application/json'}

# a real team id
_,tp=req('GET',f'{APP}/api/meta/teams-public'); TEAM=tp['teams'][0]['id']; TEAMN=tp['teams'][0]['name']
print('team under test:',TEAMN)
ADMIN='engg_himanshu2007@yahoo.co.in'
U=['sgtest1@example.com','sgtest2@example.com','sgtest3@example.com']
for e in U+[ADMIN]: auth_delete(e)
dbq("delete from signup_requests where email like 'sgtest%'; delete from allowed_emails where email like 'sgtest%'; delete from players where email like 'sgtest%';")

print('\n1) signup u1 -> /me unregistered')
t1=signup(U[0],'Passw0rd!1')
print('   /me:', req('GET',f'{APP}/api/meta/me',apph(t1))[1].get('status'))
print('2) u1 request team -> pending')
print('   request:', req('POST',f'{APP}/api/signup/request',apph(t1),{'team_id':TEAM,'full_name':'SG One'}))
print('   /me:', req('GET',f'{APP}/api/meta/me',apph(t1))[1].get('status'))

print('3) admin sees request + approves')
admin_create(ADMIN,'TmpAdmin_123!'); ta=token(ADMIN,'TmpAdmin_123!')
s,lst=req('GET',f'{APP}/api/signup/requests',apph(ta))
print('   pending count:', len([r for r in lst.get('requests',[]) if r['status']=='pending']))
print('   approve u1:', req('POST',f'{APP}/api/signup/requests/{U[0]}/approve',apph(ta)))
print('   u1 /me after approve:', req('GET',f'{APP}/api/meta/me',apph(t1))[1])

print('4) 2-per-team cap')
t2=signup(U[1],'Passw0rd!1'); req('POST',f'{APP}/api/signup/request',apph(t2),{'team_id':TEAM})
print('   approve u2:', req('POST',f'{APP}/api/signup/requests/{U[1]}/approve',apph(ta))[0])
t3=signup(U[2],'Passw0rd!1')
print('   u3 request (expect 409 team full):', req('POST',f'{APP}/api/signup/request',apph(t3),{'team_id':TEAM}))

print('\ncleanup...')
for e in U+[ADMIN]: auth_delete(e)
dbq("delete from signup_requests where email like 'sgtest%'; delete from allowed_emails where email like 'sgtest%'; delete from players where email like 'sgtest%';")
print('done')
