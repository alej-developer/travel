import { SearchPageTemplate } from "@/components/templates/SearchPageTemplate";

/**
 * Home page — renders the SearchPageTemplate (Navbar + Hero + Results).
 * This is a Server Component; interactive logic lives in client components below.
 */
export default function HomePage() {
  return <SearchPageTemplate />;
}
