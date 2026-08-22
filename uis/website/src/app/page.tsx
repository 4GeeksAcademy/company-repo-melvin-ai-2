import { Footer } from "@/components/Footer";
import { Header } from "@/components/Header";
import {
  Hero,
  Locations,
  Loyalty,
  MenuFeature,
  Pillars,
  Story,
} from "@/components/HomeSections";

export default function Home() {
  return (
    <>
      <Header />
      <main id="main">
        <Hero />
        <Story />
        <Pillars />
        <MenuFeature />
        <Locations />
        <Loyalty />
      </main>
      <Footer />
    </>
  );
}
