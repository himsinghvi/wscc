// Fixed animated mesh/aurora background rendered once behind the whole app.
export default function Aurora() {
  return (
    <div className="aurora" aria-hidden="true">
      <div className="blob3" />
      <div className="grid" />
    </div>
  )
}
