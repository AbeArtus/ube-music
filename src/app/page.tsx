import "./page.css";

export default function Home() {
  return (
    <div className="page">
      <img className="cat" src="/u.png" alt="ube logo" />
      ube-music
      <iframe className="current-song" width="80%" height="166" allow="autoplay" src="https://w.soundcloud.com/player/?url=https%3A//api.soundcloud.com/tracks/1599846087%3Fsecret_token%3Ds-PsK7UgDVYV9&color=%239c9c94&auto_play=false&hide_related=false&show_comments=true&show_user=true&show_reposts=false&show_teaser=true"></iframe>
      <iframe 
        className="current-song"
        width="80%" 
        height="200" 
        allow="autoplay" 
        src="https://w.soundcloud.com/player/?url=https%3A//api.soundcloud.com/tracks/1890825261&color=%239c9c94&auto_play=false&hide_related=false&show_comments=true&show_user=true&show_reposts=false&show_teaser=true"></iframe><div 
        style={{
          "fontSize": "10px",
          "margin": "16px",
          "color": "#cccccc",
          "lineBreak": "anywhere",
          "wordBreak": "normal",
          "overflow": "hidden",
          "whiteSpace": "nowrap",
          "textOverflow": "ellipsis",
          "fontFamily": "Interstate,Lucida Grande,Lucida Sans Unicode,Lucida Sans,Garuda,Verdana,Tahoma,sans-serif",
          "fontWeight": "100;"
      }} />
      <img className="cat" src="/catstruction.png" alt="Cat at work" />
    </div>
  );
}
