interface LogoProps {
  size?: number;
  className?: string;
}

// Brand mark: a stacked document being extracted into structured JSON nodes,
// crowned by an AI spark. Blue→cyan gradient, flat, modern SaaS style.
export function Logo({ size = 36, className = '' }: LogoProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      className={className}
      role="img"
      aria-label="ExtractIQ Engine logo"
    >
      <defs>
        <linearGradient id="eiq-grad" x1="6" y1="4" x2="42" y2="44" gradientUnits="userSpaceOnUse">
          <stop stopColor="#3B82F6" />
          <stop offset="0.55" stopColor="#06B6D4" />
          <stop offset="1" stopColor="#22C55E" />
        </linearGradient>
        <linearGradient id="eiq-grad-soft" x1="6" y1="4" x2="42" y2="44" gradientUnits="userSpaceOnUse">
          <stop stopColor="#3B82F6" stopOpacity="0.25" />
          <stop offset="1" stopColor="#06B6D4" stopOpacity="0.15" />
        </linearGradient>
      </defs>

      {/* rounded tile */}
      <rect x="3" y="3" width="42" height="42" rx="12" fill="url(#eiq-grad-soft)" />
      <rect x="3" y="3" width="42" height="42" rx="12" fill="none" stroke="url(#eiq-grad)" strokeWidth="1.2" opacity="0.5" />

      {/* document */}
      <rect x="11" y="13" width="16" height="20" rx="2.5" fill="none" stroke="url(#eiq-grad)" strokeWidth="2" />
      <line x1="14.5" y1="19" x2="23.5" y2="19" stroke="url(#eiq-grad)" strokeWidth="1.6" strokeLinecap="round" opacity="0.7" />
      <line x1="14.5" y1="23" x2="21" y2="23" stroke="url(#eiq-grad)" strokeWidth="1.6" strokeLinecap="round" opacity="0.55" />
      <line x1="14.5" y1="27" x2="23.5" y2="27" stroke="url(#eiq-grad)" strokeWidth="1.6" strokeLinecap="round" opacity="0.4" />

      {/* extraction arrow */}
      <path d="M27 23 L31.5 23" stroke="url(#eiq-grad)" strokeWidth="2" strokeLinecap="round" />
      <path d="M30 23 L33 23 L33 20 M33 23 L33 26" stroke="url(#eiq-grad)" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" opacity="0" />

      {/* structured JSON nodes (bracket + dots) */}
      <path d="M34 16 C32 16 32 18 32 20 L32 28 C32 30 30 30 30 30" stroke="url(#eiq-grad)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="35.5" cy="20" r="1.5" fill="url(#eiq-grad)" />
      <circle cx="35.5" cy="24" r="1.5" fill="url(#eiq-grad)" />
      <circle cx="35.5" cy="28" r="1.5" fill="url(#eiq-grad)" />

      {/* AI spark top-right */}
      <path
        d="M37 7 C37 9.5 38.5 11 41 11 C38.5 11 37 12.5 37 15 C37 12.5 35.5 11 33 11 C35.5 11 37 9.5 37 7 Z"
        fill="url(#eiq-grad)"
      />
    </svg>
  );
}
