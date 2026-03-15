import React from "react";
import { cn } from "@/lib/utils";
import { Share2, Link as LinkIcon, Mail } from "lucide-react";

interface ShareButtonsProps {
  title: string;
  url: string;
}

export function ShareButtons({ title, url }: ShareButtonsProps) {
  const encTitle = encodeURIComponent(title);
  const encUrl = encodeURIComponent(url);

  const links = [
    {
      name: "X",
      href: `https://twitter.com/intent/tweet?text=${encTitle}&url=${encUrl}`,
      icon: (
        <svg viewBox="0 0 24 24" className="w-4 h-4 fill-current">
          <path d="M18.901 1.153h3.68l-8.04 9.19L24 22.846h-7.406l-5.8-7.584-6.638 7.584H.474l8.6-9.83L0 1.154h7.594l5.243 6.932ZM17.61 20.644h2.039L6.486 3.24H4.298Z" />
        </svg>
      ),
    },
    {
      name: "WhatsApp",
      href: `https://api.whatsapp.com/send?text=${encTitle}%20${encUrl}`,
      icon: (
        <svg viewBox="0 0 24 24" className="w-4 h-4 fill-current">
          <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
        </svg>
      ),
    },
    {
      name: "Email",
      href: `mailto:?subject=${encTitle}&body=${encTitle}%0A%0A${encUrl}`,
      icon: <Mail className="w-4 h-4" />,
    },
  ];

  return (
    <div className="flex gap-2 items-center flex-wrap pt-4 mt-6 border-t border-stone-200">
      <span className="text-xs uppercase tracking-wider text-stone-500 font-medium mr-2 flex items-center gap-1">
        <Share2 className="w-3 h-3" />
        Share
      </span>
      {links.map((link) => (
        <a
          key={link.name}
          href={link.href}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 px-3 py-1.5 bg-stone-100/50 hover:bg-stone-900 hover:text-white text-stone-600 border border-stone-200 hover:border-stone-900 rounded transition-all text-[11px] font-mono tracking-tight"
        >
          {link.icon}
          {link.name}
        </a>
      ))}
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className="flex items-center gap-2 px-3 py-1.5 bg-stone-100/50 hover:bg-stone-900 hover:text-white text-stone-600 border border-stone-200 hover:border-stone-900 rounded transition-all text-[11px] font-mono tracking-tight ml-auto"
      >
        <LinkIcon className="w-3 h-3" />
        Open Lead
      </a>
    </div>
  );
}
