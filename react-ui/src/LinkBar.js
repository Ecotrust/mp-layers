import OverlayTrigger from "react-bootstrap/OverlayTrigger";
import Tooltip from "react-bootstrap/Tooltip";

// LinkBar component
const LinkBar = ({
  theme,
  isVisible,
  kml,
  data_download,
  metadata,
  source,
  description,
}) => {
  const handleLinkClick = (event) => {
    event.stopPropagation();
    // Further code if needed
  };
  const renderLink = (href, text, tooltip) => {
    return (
      <OverlayTrigger overlay={<Tooltip>{tooltip}</Tooltip>}>
        <span className="link-bar-content" style={{marginRight: "14px"}}>
          <a
            href={href}
            className={`link-text ${!href ? "disabled" : ""}`}
            onClick={href ? null : (e) => e.preventDefault()}
            // If href is null, prevent the default action
          >
            {text} <i className="fa fa-arrow-down"></i>
          </a>
        </span>
      </OverlayTrigger>
    );
  };
  return (
    <div
      className={`link-bar ${isVisible ? "show" : ""}`}
      style={{
        background: "#f8f8f8",
        padding: "10px",
        textAlign: "center",
        display: isVisible ? "block" : "none",
      }}
      onClick={handleLinkClick}
    >
      {renderLink(kml, "kml", "Download for Google Maps")}
      {renderLink(data_download, "data", "Download ESRI Formatted Dataset")}
      {renderLink(metadata, "metadata", "View Metadata")}
      {renderLink(source, "source", "Link to Dataset Source Provider")}
      {<div className="description-box">{description}</div>}
    </div>
  );
};

export default LinkBar;
