function InfoList({ label, items }) {
  return (
    <div className="info-box">
      <h3>{label}</h3>
      <ul>
        {items.map((item, index) => (
          <li key={`${label}-${index}`}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

export default InfoList;
