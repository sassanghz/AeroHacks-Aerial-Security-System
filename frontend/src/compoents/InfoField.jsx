function InfoField({ label, value }) {
  return (
    <div className="info-box">
      <h3>{label}</h3>
      <p>{value}</p>
    </div>
  );
}

export default InfoField;
