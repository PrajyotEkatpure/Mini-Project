"use client";
// Illustrated storybook assets, drawn as SVG so they scale cleanly and need no image generation service.
// Backgrounds are keyed by the identifiers the story schema allows; characters are parametric so the
// same character looks identical in every scene (skin/hair/outfit/accessory come from the character registry).
import React from "react";

const SKIN = { light: "#f2cba8", wheat: "#dcaa7e", brown: "#b97a4e", deep: "#7b4b31" };
const HAIR = { black: "#1d1a1e", brown: "#4b3020", grey: "#8e8e94", white: "#e9e7e2" };
const OUTFIT = { saffron: "#e98a2c", green: "#2f8f5b", blue: "#2f6fb5", maroon: "#8f2c3e", teal: "#1f8a8a", mustard: "#c9a227", navy: "#243c6c", plum: "#6e3b7b" };

const W = 1000;
const H = 560;

function Sky({ top = "#f9d9a0", bottom = "#fbeacb" }) {
  return (
    <>
      <defs>
        <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={top} />
          <stop offset="1" stopColor={bottom} />
        </linearGradient>
      </defs>
      <rect width={W} height={H} fill="url(#sky)" />
    </>
  );
}

function Floor({ color = "#c7a574", y = 420 }) {
  return <rect y={y} width={W} height={H - y} fill={color} />;
}

function Window({ x, y, w = 110, h = 130 }) {
  return (
    <g>
      <rect x={x} y={y} width={w} height={h} rx="6" fill="#bfe3f2" stroke="#7a5a3a" strokeWidth="8" />
      <line x1={x + w / 2} y1={y} x2={x + w / 2} y2={y + h} stroke="#7a5a3a" strokeWidth="6" />
      <line x1={x} y1={y + h / 2} x2={x + w} y2={y + h / 2} stroke="#7a5a3a" strokeWidth="6" />
    </g>
  );
}

const Flag = ({ x, y }) => (
  <g>
    <rect x={x} y={y} width="6" height="150" fill="#6b5a45" />
    <rect x={x + 6} y={y} width="84" height="18" fill="#e98a2c" />
    <rect x={x + 6} y={y + 18} width="84" height="18" fill="#fff" />
    <rect x={x + 6} y={y + 36} width="84" height="18" fill="#2f8f5b" />
    <circle cx={x + 48} cy={y + 27} r="6" fill="none" stroke="#243c6c" strokeWidth="1.5" />
  </g>
);

const BACKGROUNDS = {
  village_square: () => (
    <>
      <Sky top="#8fd0ee" bottom="#fde7b8" />
      <circle cx="840" cy="110" r="52" fill="#fff3b0" />
      <path d="M0 360 Q250 300 500 350 T1000 330 V420 H0Z" fill="#8ec27a" />
      <Floor color="#d9b784" y={410} />
      <rect x="90" y="250" width="200" height="160" fill="#e7c9a0" />
      <polygon points="70,255 190,170 310,255" fill="#b0523a" />
      <rect x="165" y="320" width="50" height="90" fill="#7a5a3a" />
      <rect x="640" y="280" width="26" height="140" fill="#6b4a2c" />
      <circle cx="653" cy="250" r="90" fill="#4f9d5e" />
      <circle cx="600" cy="285" r="55" fill="#5fb26d" />
      <ellipse cx="500" cy="480" rx="260" ry="26" fill="#cda973" opacity=".6" />
    </>
  ),
  school_classroom: () => (
    <>
      <rect width={W} height={H} fill="#f3e3c4" />
      <rect x="0" y="0" width={W} height="40" fill="#e0c9a0" />
      <rect x="170" y="70" width="520" height="210" rx="8" fill="#2e5d4b" stroke="#8a6a44" strokeWidth="10" />
      <text x="430" y="150" textAnchor="middle" fill="#e8f3ee" fontSize="34" fontFamily="'Comic Sans MS','Segoe Print',cursive" opacity=".85">Our Constitution</text>
      <line x1="260" y1="190" x2="600" y2="190" stroke="#e8f3ee" strokeWidth="3" opacity=".5" strokeDasharray="10 8" />
      <Window x={780} y={80} />
      <Floor color="#b78d5c" y={400} />
      <rect x="70" y="360" width="200" height="16" fill="#8a6a44" />
      <rect x="85" y="376" width="10" height="60" fill="#6f5233" />
      <rect x="245" y="376" width="10" height="60" fill="#6f5233" />
      <Flag x={860} y={250} />
    </>
  ),
  courtroom: () => (
    <>
      <rect width={W} height={H} fill="#d9c3a0" />
      <rect x="0" y="0" width={W} height="60" fill="#8a5a3a" />
      {[120, 280, 440, 600, 760].map((x) => (
        <rect key={x} x={x} y="60" width="40" height="340" fill="#c9ad84" stroke="#a88b62" strokeWidth="3" />
      ))}
      <rect x="330" y="230" width="340" height="170" fill="#7a4a2c" />
      <rect x="310" y="215" width="380" height="26" fill="#5e371f" />
      <circle cx="500" cy="150" r="46" fill="#f1e2bc" stroke="#7a5a3a" strokeWidth="6" />
      <line x1="500" y1="115" x2="500" y2="185" stroke="#7a5a3a" strokeWidth="5" />
      <line x1="470" y1="130" x2="530" y2="130" stroke="#7a5a3a" strokeWidth="5" />
      <Floor color="#8a5a3a" y={400} />
    </>
  ),
  city_street: () => (
    <>
      <Sky top="#9ad7ef" bottom="#fde9c4" />
      {[[40, 150, 170], [230, 110, 210], [470, 170, 150], [660, 120, 200], [850, 160, 160]].map(([x, y, w], i) => (
        <g key={i}>
          <rect x={x} y={y + 80} width={w} height={340 - y} fill={["#d98c6a", "#e9b66c", "#c7776a", "#e2a37a", "#cf9a6a"][i]} />
          {[0, 1, 2].map((r) => (
            <rect key={r} x={x + 22} y={y + 105 + r * 62} width="34" height="38" fill="#fff0c8" stroke="#6b4a2c" strokeWidth="3" />
          ))}
        </g>
      ))}
      <rect y="400" width={W} height="160" fill="#6a6a72" />
      <rect y="396" width={W} height="14" fill="#bdb6a8" />
      {[60, 260, 460, 660, 860].map((x) => (
        <rect key={x} x={x} y="490" width="90" height="10" fill="#f5e9c0" />
      ))}
    </>
  ),
  home_interior: () => (
    <>
      <rect width={W} height={H} fill="#f4dcc0" />
      <rect y="410" width={W} height="150" fill="#b98a5a" />
      <Window x={90} y={90} w={150} h={150} />
      <rect x="400" y="260" width="360" height="130" rx="14" fill="#a9503f" />
      <rect x="400" y="215" width="360" height="70" rx="14" fill="#bd6350" />
      <rect x="820" y="110" width="90" height="120" fill="#fbf0d6" stroke="#8a6a44" strokeWidth="8" />
      <circle cx="865" cy="170" r="22" fill="#e98a2c" />
      <rect x="445" y="390" width="12" height="30" fill="#6f5233" />
      <rect x="700" y="390" width="12" height="30" fill="#6f5233" />
    </>
  ),
  market: () => (
    <>
      <Sky top="#9ad7ef" bottom="#fde9c4" />
      {[[40, "#e9822c"], [360, "#2f8f5b"], [680, "#b83a4b"]].map(([x, c], i) => (
        <g key={i}>
          <polygon points={`${x},150 ${x + 290},150 ${x + 320},210 ${x - 30},210`} fill={c} />
          {[0, 1, 2, 3, 4, 5].map((k) => (
            <polygon key={k} points={`${x - 30 + k * 58},210 ${x + 28 + k * 58},210 ${x + 14 + k * 58},232`} fill={k % 2 ? "#fff6df" : c} />
          ))}
          <rect x={x} y="260" width="260" height="130" fill="#a4733f" />
          {[0, 1, 2, 3].map((k) => (
            <circle key={k} cx={x + 45 + k * 55} cy="252" r="22" fill={["#e53935", "#f6a623", "#7cb342", "#f6a623"][(k + i) % 4]} />
          ))}
        </g>
      ))}
      <Floor color="#cfa873" y={420} />
    </>
  ),
  parliament: () => (
    <>
      <Sky top="#a8d9ee" bottom="#fdeccc" />
      <rect x="150" y="260" width="700" height="170" fill="#e7cfa2" />
      <circle cx="500" cy="262" r="120" fill="#e0bf8a" />
      <path d="M380 262 A120 120 0 0 1 620 262Z" fill="#d6b074" />
      <rect x="494" y="120" width="12" height="40" fill="#6b5a45" />
      {Array.from({ length: 12 }).map((_, i) => (
        <rect key={i} x={180 + i * 56} y="290" width="22" height="140" fill="#f3e2bd" stroke="#c9ad84" strokeWidth="2" />
      ))}
      <Floor color="#c8a876" y={430} />
      <Flag x={60} y={240} />
    </>
  ),
  office: () => (
    <>
      <rect width={W} height={H} fill="#e6e0d2" />
      <rect y="420" width={W} height="140" fill="#9a8466" />
      <Window x={120} y={90} w={170} h={140} />
      <rect x="380" y="300" width="380" height="24" fill="#6b4a2c" />
      <rect x="400" y="324" width="12" height="100" fill="#5a3d24" />
      <rect x="730" y="324" width="12" height="100" fill="#5a3d24" />
      <rect x="500" y="240" width="110" height="60" rx="4" fill="#33424f" />
      <rect x="540" y="300" width="30" height="8" fill="#33424f" />
      <rect x="820" y="130" width="100" height="270" fill="#8a6a44" />
      {[0, 1, 2, 3].map((k) => (
        <rect key={k} x="830" y={145 + k * 62} width="80" height="8" fill="#c9ad84" />
      ))}
    </>
  ),
  railway_station: () => (
    <>
      <Sky top="#9ad7ef" bottom="#fde9c4" />
      <rect x="0" y="120" width={W} height="30" fill="#7a5a3a" />
      {[100, 400, 700].map((x) => (
        <rect key={x} x={x} y="150" width="16" height="270" fill="#8a6a44" />
      ))}
      <rect x="0" y="340" width={W} height="90" fill="#555a63" />
      <rect y="420" width={W} height="140" fill="#bfb7a6" />
      <rect y="420" width={W} height="10" fill="#f0d34a" />
      <rect x="560" y="190" width="380" height="150" rx="10" fill="#2f6fb5" />
      {[0, 1, 2].map((k) => (
        <rect key={k} x={590 + k * 115} y="215" width="80" height="60" fill="#d8f0fb" />
      ))}
      <rect x="140" y="230" width="150" height="50" rx="4" fill="#243c6c" />
      <text x="215" y="263" textAnchor="middle" fill="#fff" fontSize="22" fontFamily="sans-serif">PLATFORM 1</text>
    </>
  ),
  library: () => (
    <>
      <rect width={W} height={H} fill="#e9d3ae" />
      <rect y="430" width={W} height="130" fill="#8f6a44" />
      {[0, 1, 2].map((s) => (
        <g key={s}>
          <rect x={60 + s * 300} y="70" width="260" height="350" fill="#6b4a2c" />
          {[0, 1, 2, 3].map((r) => (
            <g key={r}>
              <rect x={72 + s * 300} y={90 + r * 82} width="236" height="6" fill="#4d331c" />
              {Array.from({ length: 9 }).map((_, b) => (
                <rect key={b} x={78 + s * 300 + b * 25} y={r * 82 + 40} width="18" height="50" fill={["#b83a4b", "#2f6fb5", "#c9a227", "#2f8f5b", "#6e3b7b"][(b + r + s) % 5]} />
              ))}
            </g>
          ))}
        </g>
      ))}
    </>
  ),
};

export function Background({ id }) {
  const Scene = BACKGROUNDS[id] || BACKGROUNDS.village_square;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="xMidYMid slice" className="absolute inset-0 h-full w-full" aria-hidden="true">
      <Scene />
      <rect width={W} height={H} fill="url(#vig)" />
      <defs>
        <radialGradient id="vig" cx="50%" cy="45%" r="75%">
          <stop offset="60%" stopColor="#000" stopOpacity="0" />
          <stop offset="100%" stopColor="#1b1020" stopOpacity=".28" />
        </radialGradient>
      </defs>
    </svg>
  );
}

function Face({ emotion, speaking }) {
  const mouth = {
    happy: "M-14 22 Q0 38 14 22",
    curious: "M-8 28 Q0 24 8 28",
    worried: "M-12 32 Q0 22 12 32",
    surprised: null,
    thoughtful: "M-9 28 L9 26",
    determined: "M-12 28 L12 28",
    neutral: "M-11 27 Q0 33 11 27",
  }[emotion];
  const brow = {
    worried: ["M-26 -10 L-10 -16", "M26 -10 L10 -16"],
    determined: ["M-26 -16 L-10 -10", "M26 -16 L10 -10"],
    curious: ["M-26 -14 L-10 -14", "M26 -20 L10 -16"],
    surprised: ["M-26 -22 L-10 -22", "M26 -22 L10 -22"],
  }[emotion] || ["M-26 -14 L-10 -14", "M26 -14 L10 -14"];
  return (
    <g>
      <ellipse cx="-17" cy="0" rx="5.5" ry={emotion === "surprised" ? 8 : 6.5} fill="#1a1316" />
      <ellipse cx="17" cy="0" rx="5.5" ry={emotion === "surprised" ? 8 : 6.5} fill="#1a1316" />
      <circle cx="-15" cy="-2" r="1.8" fill="#fff" />
      <circle cx="19" cy="-2" r="1.8" fill="#fff" />
      {brow.map((d, i) => (
        <path key={i} d={d} stroke="#1a1316" strokeWidth="3.4" strokeLinecap="round" fill="none" />
      ))}
      {mouth ? (
        <path d={mouth} stroke="#6b2a2a" strokeWidth="3.4" strokeLinecap="round" fill={speaking && emotion === "happy" ? "#a33" : "none"} />
      ) : (
        <ellipse cx="0" cy="30" rx="7" ry="9" fill="#6b2a2a" />
      )}
      <ellipse cx="-30" cy="18" rx="8" ry="5" fill="#e37b6b" opacity=".35" />
      <ellipse cx="30" cy="18" rx="8" ry="5" fill="#e37b6b" opacity=".35" />
    </g>
  );
}

function Arms({ pose, outfit, skin }) {
  const sleeve = outfit;
  const arm = (d) => <path d={d} stroke={sleeve} strokeWidth="26" strokeLinecap="round" fill="none" />;
  const hand = (x, y) => <circle cx={x} cy={y} r="13" fill={skin} />;
  switch (pose) {
    case "pointing":
      return (
        <g>
          {arm("M-52 150 Q-70 200 -66 250")}{hand(-66, 256)}
          {arm("M52 150 Q110 150 150 118")}{hand(156, 112)}
          <path d="M162 108 L190 96" stroke={skin} strokeWidth="9" strokeLinecap="round" />
        </g>
      );
    case "thinking":
      return (
        <g>
          {arm("M-52 150 Q-70 200 -66 250")}{hand(-66, 256)}
          {arm("M52 150 Q90 190 36 110")}{hand(30, 104)}
        </g>
      );
    case "reading":
      return (
        <g>
          {arm("M-52 150 Q-76 200 -30 214")}{arm("M52 150 Q76 200 30 214")}
          <rect x="-44" y="186" width="88" height="56" rx="4" fill="#f6efe0" stroke="#7a5a3a" strokeWidth="4" />
          <line x1="0" y1="186" x2="0" y2="242" stroke="#7a5a3a" strokeWidth="3" />
          {hand(-34, 218)}{hand(34, 218)}
        </g>
      );
    case "talking":
      return (
        <g>
          {arm("M-52 150 Q-70 200 -66 250")}{hand(-66, 256)}
          {arm("M52 150 Q96 168 92 214")}{hand(92, 222)}
        </g>
      );
    default:
      return (
        <g>
          {arm("M-52 150 Q-70 200 -66 250")}{hand(-66, 256)}
          {arm("M52 150 Q70 200 66 250")}{hand(66, 256)}
        </g>
      );
  }
}

export function CharacterFigure({ character, emotion = "neutral", pose = "standing", speaking = false, mirrored = false }) {
  const skin = SKIN[character.skin] || SKIN.wheat;
  const hair = HAIR[character.hair] || HAIR.black;
  const outfit = OUTFIT[character.outfit] || OUTFIT.blue;
  const acc = character.accessory;
  return (
    <svg viewBox="-130 -110 320 600" className="h-full w-auto overflow-visible" role="img" aria-label={`${character.name}, ${character.role}`}>
      <g transform={mirrored ? "scale(-1,1) translate(-60,0)" : undefined}>
        <ellipse cx="0" cy="478" rx="90" ry="12" fill="#000" opacity=".18" />
        <path d="M-40 270 L-44 470 L-8 470 L0 300 L8 470 L44 470 L40 270Z" fill="#3a3550" />
        <rect x="-56" y="448" width="52" height="24" rx="8" fill="#2a2432" />
        <rect x="4" y="448" width="52" height="24" rx="8" fill="#2a2432" />
        <path d="M-58 150 Q-60 130 -26 124 L26 124 Q60 130 58 150 L60 300 L-60 300Z" fill={outfit} />
        {acc === "dupatta" && <path d="M-50 132 Q0 190 60 150 L60 170 Q0 230 -50 160Z" fill="#fff" opacity=".75" />}
        {acc === "robe" && <path d="M-58 150 L58 150 L60 300 L-60 300Z M-10 124 L0 300 L10 124Z" fill="#1c1c24" />}
        <path d="M-12 120 L12 120 L12 146 L-12 146Z" fill={skin} />
        <Arms pose={pose} outfit={acc === "robe" ? "#1c1c24" : outfit} skin={skin} />
        <g transform={speaking ? "translate(0,-4)" : undefined}>
          <circle cx="0" cy="40" r="66" fill={skin} />
          <path d="M-68 36 Q-70 -34 0 -38 Q70 -34 68 36 Q50 -2 0 -4 Q-50 -2 -68 36Z" fill={hair} />
          {acc === "turban" && <path d="M-72 30 Q-76 -52 0 -58 Q76 -52 72 30 Q40 6 0 6 Q-40 6 -72 30Z" fill="#c9582a" />}
          {acc === "cap" && <path d="M-70 24 Q-70 -44 0 -46 Q70 -44 70 24Z M-70 24 L-92 30 L-70 38Z" fill="#2f6fb5" />}
          <g transform="translate(0,34)">
            <Face emotion={emotion} speaking={speaking} />
            {acc === "glasses" && (
              <g stroke="#333" strokeWidth="3.5" fill="#fff" fillOpacity=".25">
                <circle cx="-17" cy="0" r="14" />
                <circle cx="17" cy="0" r="14" />
                <line x1="-3" y1="0" x2="3" y2="0" />
              </g>
            )}
          </g>
        </g>
      </g>
    </svg>
  );
}
