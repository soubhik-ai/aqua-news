import type { Metadata } from "next";
import { Inter, Playfair_Display } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const playfair = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-playfair",
});

export const metadata: Metadata = {
  title: "AQUA NEWS | Unbiased, Multi-source Clustering",
  description:
    "A premium, AI-free news aggregator clustering stories from 28 sources to expose bias and find the center.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="antialiased">
      <body
        className={`${inter.variable} ${playfair.variable} font-sans bg-stone-50 text-stone-900 min-h-screen`}
      >
        {children}
      </body>
    </html>
  );
}
