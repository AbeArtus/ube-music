import "./page.css";
import Image from "next/image";

export default function Home() {
  return (
    <div className="page">
      <img className="cat" src="/u.png" alt="ube logo" />
      ube-music
      <iframe 
        className="sc-player"
        width="80%"
        height="166"
        allow="autoplay"
        src="https://w.soundcloud.com/player/?url=https%3A//api.soundcloud.com/tracks/1872600960&color=%23ff0000&auto_play=true&hide_related=true&show_comments=true&show_user=false&show_reposts=false&show_teaser=false">
      </iframe>
      <iframe 
        className="sc-player"
        width="80%"
        height="166"
        src="https://w.soundcloud.com/player/?url=https%3A//api.soundcloud.com/tracks/1599846087%3Fsecret_token%3Ds-PsK7UgDVYV9&color=%239c9c94&auto_play=false&hide_related=true&show_comments=false&show_user=false&show_reposts=false&show_teaser=false"
      >
      </iframe>
      <iframe 
        className="sc-player"
        width="80%" 
        height="166" 
        src="https://w.soundcloud.com/player/?url=https%3A//api.soundcloud.com/tracks/1890825261&color=%239c9c94&auto_play=false&hide_related=true&show_comments=false&show_user=true&show_reposts=true&show_teaser=false"></iframe><div 
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
          "fontWeight": "100"
        }}
      />
      <Image className="cat" src="/catstruction.png" alt="Cat at work" width={500} height={500} />
    </div>
  );
}
