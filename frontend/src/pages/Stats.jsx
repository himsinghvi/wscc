import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { get } from '../api/client'
import FormBadges from '../components/FormBadges'
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid,
  LineChart, Line, PieChart, Pie, Cell, Legend,
} from 'recharts'

const COLORS = ['#4f8cff', '#22c55e', '#f59e0b', '#ef4444', '#a855f7', '#06b6d4']
const axis = { stroke: '#9fb0cd', fontSize: 12 }
const tip = { background: '#121c33', border: '1px solid #26324f', borderRadius: 8, color: '#e8eef9' }

export default function Stats() {
  const [s, setS] = useState(null)
  const [team, setTeam] = useState('')

  const load = (t) => get('/stats/overview', t ? { team_id: t } : undefined).then(setS).catch(() => {})
  useEffect(() => { load('') }, [])

  if (!s) return <div className="spinner-border text-primary" />

  const onTeam = (e) => { setTeam(e.target.value); load(e.target.value) }

  return (
    <>
      <h3 className="fw-bold mb-4">Statistics</h3>

      {/* Standings */}
      <div className="card wscc mb-4"><div className="card-body">
        <h6 className="mb-3"><i className="bi bi-list-ol me-1" />League standings</h6>
        <div className="table-responsive">
          <table className="table table-sm align-middle mb-0">
            <thead><tr className="text-muted-2 small">
              <th>#</th><th>Team</th><th className="text-center">P</th><th className="text-center">W</th>
              <th className="text-center">L</th><th className="text-center">Pts</th><th>Form</th>
            </tr></thead>
            <tbody>
              {s.standings.map((r) => (
                <tr key={r.team_id}>
                  <td>{r.position}</td>
                  <td><Link to={`/teams/${r.team_id}`} className="text-decoration-none fw-semibold">{r.team}</Link></td>
                  <td className="text-center">{r.played}</td>
                  <td className="text-center text-success">{r.won}</td>
                  <td className="text-center text-danger">{r.lost}</td>
                  <td className="text-center fw-bold">{r.points}</td>
                  <td><FormBadges form={r.form} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div></div>

      <div className="row g-4">
        <div className="col-lg-7">
          <Panel title="Matches played by month">
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={s.matches_by_month}>
                <CartesianGrid strokeDasharray="3 3" stroke="#26324f" />
                <XAxis dataKey="month" {...axis} /><YAxis {...axis} allowDecimals={false} />
                <Tooltip contentStyle={tip} />
                <Line type="monotone" dataKey="played" stroke="#4f8cff" strokeWidth={3} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </Panel>
        </div>
        <div className="col-lg-5">
          <Panel title="Ground usage">
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie data={s.ground_usage} dataKey="matches" nameKey="ground" outerRadius={90} label>
                  {s.ground_usage.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Legend wrapperStyle={{ color: '#9fb0cd', fontSize: 12 }} />
                <Tooltip contentStyle={tip} />
              </PieChart>
            </ResponsiveContainer>
          </Panel>
        </div>
        <div className="col-12">
          <div className="card wscc"><div className="card-body">
            <div className="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
              <h6 className="mb-0">Head-to-head record (played / won)</h6>
              <select className="form-select form-select-sm" style={{ width: 'auto' }} value={team} onChange={onTeam}>
                <option value="">{s.standings[0]?.team} (top team)</option>
                {s.standings.map((r) => <option key={r.team_id} value={r.team_id}>{r.team}</option>)}
              </select>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={s.my_team_vs_others}>
                <CartesianGrid strokeDasharray="3 3" stroke="#26324f" />
                <XAxis dataKey="opponent" {...axis} /><YAxis {...axis} allowDecimals={false} />
                <Tooltip contentStyle={tip} /><Legend wrapperStyle={{ color: '#9fb0cd' }} />
                <Bar dataKey="played" fill="#4f8cff" radius={[6, 6, 0, 0]} />
                <Bar dataKey="won" fill="#22c55e" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div></div>
        </div>
      </div>
    </>
  )
}

function Panel({ title, children }) {
  return <div className="card wscc h-100"><div className="card-body"><h6 className="mb-3">{title}</h6>{children}</div></div>
}
