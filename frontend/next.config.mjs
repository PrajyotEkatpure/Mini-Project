/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    // Import only the icons that are used instead of compiling each whole icon pack (keeps dev memory low).
    optimizePackageImports: [
      "react-icons/ai", "react-icons/ci", "react-icons/fa", "react-icons/fa6", "react-icons/go",
      "react-icons/gi", "react-icons/md", "react-icons/pi", "react-icons/ri", "lucide-react",
    ],
  },
};

export default nextConfig; 
