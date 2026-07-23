export const locations = {
  Colombia: [
    "El Poblado",
    "Laureles",
    "Envigado",
    "Sabaneta",
    "Usaquén",
    "Chapinero",
    "Zona Rosa",
    "Granada",
    "Ciudad Jardín",
    "Unicentro",
  ],
  "United States": [
    "Brickell",
    "Coral Gables",
    "Downtown Orlando",
    "International Drive",
  ],
} as const;

export const citiesByCountry = {
  Colombia: ["Medellín", "Bogotá", "Cali"],
  "United States": ["Miami", "Orlando"],
} as const;

export const locationsByCity: Record<string, string[]> = {
  Medellín: ["El Poblado", "Laureles", "Envigado", "Sabaneta"],
  Bogotá: ["Usaquén", "Chapinero", "Zona Rosa"],
  Cali: ["Granada", "Ciudad Jardín", "Unicentro"],
  Miami: ["Brickell", "Coral Gables"],
  Orlando: ["Downtown Orlando", "International Drive"],
};

export const pillars = [
  {
    number: "01",
    title: "Consistent quality",
    text: "The same trusted recipes, standards, and fresh ingredients in every kitchen.",
  },
  {
    number: "02",
    title: "Warm experience",
    text: "Friendly, attentive service and a family atmosphere on every visit.",
  },
  {
    number: "03",
    title: "Ready with purpose",
    text: "Food prepared quickly without sacrificing flavor, care, or quality.",
  },
];
