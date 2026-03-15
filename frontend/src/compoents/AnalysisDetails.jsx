import InfoField from "./InfoField";
import InfoList from "./InfoList";

function AnalysisDetails({ data }) {
  return (
    <div className="analysis-details">
      <InfoField label="Age" value={data.age} />
      <InfoField label="Skin Tone" value={data.skin_tone} />
      <InfoList label="Facial Features" items={data.facial_features} />
      <InfoList label="Clothing" items={data.clothing} />
      <InfoList label="Injuries or Condition" items={data.injuries_or_condition} />
      <InfoList label="Uncertainty" items={data.uncertainty} />
    </div>
  );
}

export default AnalysisDetails;
