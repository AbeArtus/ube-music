"use client"; 
import "./page.css";
import Image from "next/image";
import { useEffect } from "react";
import { useCallback } from "react";
import { Engine } from "tsparticles-engine";
import { Particles } from "react-particles";
import { CreateParticle } from "@/components/particle";
import { useRef } from "react";
import { loadSlim } from "tsparticles-slim";

export default function Home() {
  const particlesInit = useCallback(async (engine: Engine) => {
    await loadSlim(engine);
}, []);
  const ImageRef = useRef<HTMLImageElement>(null);


  useEffect(() => {
    const interval = setInterval(() => {
      if (ImageRef?.current?.getBoundingClientRect()) {
        const rect = ImageRef.current.getBoundingClientRect();
        // random int between 1 and 0
        const catsNumber = Math.floor(Math.random() * 2) === 0 ? .25 : .45;
        const baosNumber = Math.floor(Math.random() * 2) === 0 ? .35 : .65;
        const x = rect.left + rect.width * catsNumber + Math.random() * rect.width * .20;
        const y = rect.top + rect.height * baosNumber + Math.random() * rect.height * .20;
        CreateParticle(x,y)
      }
    }, 200); // Adjust the interval as needed

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="page">
      <Particles
            id="tsparticles"
            init={particlesInit}
            options={{
                fpsLimit: 60,
                interactivity: {
                    events: {
                        onClick: {
                            enable: true,
                            mode: "push",
                        },
                        onHover: {
                            enable: true,
                            mode: "repulse",
                        },
                        resize: true,
                    },
                    modes: {
                        push: {
                            quantity: 4,
                        },
                        repulse: {
                            distance: 50,
                            duration: 0.4,
                        },
                    },
                },
                particles: {
                    color: {
                        value: "#ffffff",
                    },
                    links: {
                        color: "#ffffff",
                        distance: 150,
                        enable: true,
                        opacity: 0.2,
                        width: 1,
                    },
                    move: {
                        direction: "none",
                        enable: true,
                        outModes: {
                            default: "bounce",
                        },
                        random: true,
                        speed: 1,
                        straight: true,
                    },
                    number: {
                        density: {
                            enable: true,
                            area: 200,
                        },
                        value: 80,
                    },
                    opacity: {
                        value: 0.1,
                    },
                    shape: {
                        type: "circle",
                    },
                    size: {
                        value: { min: 1, max: 2 },
                    },
                },
                detectRetina: true,
            }}
        />
      <Image priority ref={ImageRef} className="cat" src="/u.png" alt="ube logo" width={400} height={320} />
      <iframe 
        className="sc-player"
        width="80%"
        height="166"
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
          "fontWeight": "100",
          "border": "none"
        }}
        src="https://w.soundcloud.com/player/?url=https%3A//api.soundcloud.com/tracks/1872600960&color=%239c9c94&auto_play=false&hide_related=true&show_comments=true&show_user=false&show_reposts=false&show_teaser=false">
      </iframe>
      <iframe 
        className="sc-player"
        width="80%"
        height="166"
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
          "fontWeight": "100",
          "border": "none"
        }}
        src="https://w.soundcloud.com/player/?url=https%3A//api.soundcloud.com/tracks/1599846087%3Fsecret_token%3Ds-PsK7UgDVYV9&color=%239c9c94&auto_play=false&hide_related=true&show_comments=false&show_user=false&show_reposts=false&show_teaser=false"
      >
      </iframe>
      <iframe 
        className="sc-player"
        width="80%" 
        height="166" 
        src="https://w.soundcloud.com/player/?url=https%3A//api.soundcloud.com/tracks/1890825261%3Fsecret_token%3Ds-PsK7UgDVYV9&color=%239c9c94&color=%239c9c94&auto_play=false&hide_related=true&show_comments=false&show_user=false&show_reposts=false&show_teaser=false"></iframe><div 
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
          "fontWeight": "100",
          "border": "none"
        }}
      />
      <Image priority className="cat" src="/catstruction.png" alt="Cat at work" width={500} height={500} />
    </div>
  );
}
