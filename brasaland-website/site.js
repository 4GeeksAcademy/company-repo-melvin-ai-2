// site.js - Brasaland bilingual, validation, and dynamic logic

const dictionary = {
  en: {
    nav: {
      home: "Home",
      locations: "Locations",
      menu: "Menu",
      points: "Brasa Points",
      contact: "Contact",
    },
    common: {
      back: "Back to Home",
    },
    pageTitle: {
      index: "Brasaland | Grilled Flavor Across Colombia and the US",
      signup: "Brasa Points Registration | Brasaland",
      locations: "Brasaland Locations | Colombia and United States",
    },
    hero: {
      headline: "The taste of the grill, in every bite",
      subheadline:
        "Since 2008 serving the best grilled meats in Colombia and the United States. 14 locations, one passion for quality and flavor.",
      cta: "Join Brasa Points",
      secondaryCta: "See locations",
    },
    story: {
      title: "Our Story",
      body: "Founded in Medellin in 2008, Brasaland began as a family dream: sharing the authentic taste of grilled meat with consistent quality and warm service. Today we are 14 restaurants in two countries, but we maintain the same recipe for success: fresh products, traditional techniques, and passion for every dish we serve.",
    },
    unique: {
      title: "What Makes Us Unique",
      quality: {
        title: "Consistent Quality",
        line1: "Same recipes and standards in all locations",
        line2: "Fresh ingredients selected daily",
      },
      experience: {
        title: "Warm Experience",
        line1: "Friendly and attentive service",
        line2: "Family atmosphere on every visit",
      },
      speed: {
        title: "Speed",
        line1: "Your food ready in minutes",
        line2: "Without sacrificing flavor or quality",
      },
    },
    locations: {
      title: "Our Locations",
      hours: "Hours: Mon-Sun 11:00 AM - 10:00 PM",
      colombia: {
        title: "Colombia",
        count: "10 restaurants in Medellin, Bogota and Cali",
      },
      us: {
        title: "United States (Florida)",
        count: "4 restaurants in Miami and Orlando",
      },
    },
    locationsPage: {
      title: "Our 14 Locations",
      subtitle:
        "Visit Brasaland in Colombia and the United States. We deliver consistent quality, warm service, and fast attention in every restaurant.",
    },
    points: {
      title: "Earn points with every visit",
      line1: "Accumulate 1 point for every $10,000 COP or $5 USD",
      line2: "Redeem your points for discounts and free dishes",
      line3: "Exclusive offers for members",
      line4: "100% digital registration - no more paper cards!",
      cta: "Sign up for Brasa Points",
      notice:
        "Want to place an order? Call your favorite location or visit us directly. Online ordering coming soon!",
    },
    form: {
      title: "Join Brasa Points",
      subtitle:
        "Register once and start earning rewards in any Brasaland location in Colombia and the United States.",
      fullName: "Full name *",
      email: "Email *",
      phone: "Phone *",
      country: "Country *",
      city: "City *",
      favoriteLocation: "Favorite Brasaland location",
      dietary: "Dietary preferences",
      dietaryNoRestrictions: "No restrictions",
      dietaryVegetarian: "Vegetarian",
      dietaryGlutenFree: "Gluten-free",
      dietaryOther: "Other",
      howFound: "How did you find us? *",
      howFoundSelect: "Select one option",
      howFoundSocial: "Social media",
      howFoundRecommendation: "Recommendation",
      howFoundWalkedBy: "Walked by",
      howFoundSearch: "Internet search",
      dob: "Date of birth *",
      acceptTerms: "I accept Brasa Points program terms *",
      receiveOffers: "I want to receive offers via email",
      submit: "Register",
      clear: "Clear form",
      selectCountry: "Select your country",
      selectCity: "Select your city",
      selectFavoriteLocation: "Select your favorite location (optional)",
    },
    footer: {
      copy: "© 2025 Brasaland. All rights reserved.",
    },
  },
  es: {
    nav: {
      home: "Inicio",
      locations: "Ubicaciones",
      menu: "Menu",
      points: "Brasa Points",
      contact: "Contacto",
    },
    common: {
      back: "Volver al inicio",
    },
    pageTitle: {
      index: "Brasaland | Sabor a la parrilla en Colombia y Estados Unidos",
      signup: "Registro Brasa Points | Brasaland",
      locations: "Sedes Brasaland | Colombia y Estados Unidos",
    },
    hero: {
      headline: "El sabor de la parrilla, en cada bocado",
      subheadline:
        "Desde 2008 sirviendo las mejores carnes a la parrilla en Colombia y Estados Unidos. 14 sedes, una sola pasion por la calidad y el sabor.",
      cta: "Unete a Brasa Points",
      secondaryCta: "Ver ubicaciones",
    },
    story: {
      title: "Nuestra Historia",
      body: "Fundada en Medellin en 2008, Brasaland nacio como un sueno familiar: compartir el sabor autentico de la carne a la parrilla con calidad consistente y servicio calido. Hoy somos 14 restaurantes en dos paises, y mantenemos la misma receta de exito: productos frescos, tecnicas tradicionales y pasion por cada plato.",
    },
    unique: {
      title: "Que Nos Hace Unicos",
      quality: {
        title: "Calidad Consistente",
        line1: "Mismas recetas y estandares en todas las sedes",
        line2: "Ingredientes frescos seleccionados cada dia",
      },
      experience: {
        title: "Experiencia Calida",
        line1: "Servicio amable y atento",
        line2: "Ambiente familiar en cada visita",
      },
      speed: {
        title: "Rapidez",
        line1: "Tu comida lista en minutos",
        line2: "Sin sacrificar sabor ni calidad",
      },
    },
    locations: {
      title: "Nuestras Ubicaciones",
      hours: "Horario: Lun-Dom 11:00 AM - 10:00 PM",
      colombia: {
        title: "Colombia",
        count: "10 restaurantes en Medellin, Bogota y Cali",
      },
      us: {
        title: "Estados Unidos (Florida)",
        count: "4 restaurantes en Miami y Orlando",
      },
    },
    locationsPage: {
      title: "Nuestras 14 Sedes",
      subtitle:
        "Visita Brasaland en Colombia y Estados Unidos. Ofrecemos calidad consistente, servicio calido y atencion rapida en cada restaurante.",
    },
    points: {
      title: "Gana puntos con cada visita",
      line1: "Acumula 1 punto por cada $10.000 COP o $5 USD",
      line2: "Redime tus puntos por descuentos y platos gratis",
      line3: "Ofertas exclusivas para miembros",
      line4: "Registro 100% digital: no mas tarjetas de papel",
      cta: "Registrate en Brasa Points",
      notice:
        "Quieres hacer un pedido? Llama a tu sede favorita o visitanos directamente. Pedidos en linea proximamente.",
    },
    form: {
      title: "Unete a Brasa Points",
      subtitle:
        "Registrate una vez y empieza a ganar recompensas en cualquier sede de Brasaland en Colombia y Estados Unidos.",
      fullName: "Nombre completo *",
      email: "Correo electronico *",
      phone: "Telefono *",
      country: "Pais *",
      city: "Ciudad *",
      favoriteLocation: "Sede Brasaland favorita",
      dietary: "Preferencias alimentarias",
      dietaryNoRestrictions: "Sin restricciones",
      dietaryVegetarian: "Vegetariano",
      dietaryGlutenFree: "Sin gluten",
      dietaryOther: "Otro",
      howFound: "Como nos encontraste? *",
      howFoundSelect: "Selecciona una opcion",
      howFoundSocial: "Redes sociales",
      howFoundRecommendation: "Recomendacion",
      howFoundWalkedBy: "Pasaba por aqui",
      howFoundSearch: "Busqueda en internet",
      dob: "Fecha de nacimiento *",
      acceptTerms: "Acepto los terminos del programa Brasa Points *",
      receiveOffers: "Quiero recibir ofertas por correo",
      submit: "Registrarme",
      clear: "Limpiar formulario",
      selectCountry: "Selecciona tu pais",
      selectCity: "Selecciona tu ciudad",
      selectFavoriteLocation: "Selecciona tu sede favorita (opcional)",
    },
    footer: {
      copy: "© 2025 Brasaland. Todos los derechos reservados.",
    },
  },
};

let currentLang = localStorage.getItem("brasaland-lang") || "en";

function t(path) {
  return path
    .split(".")
    .reduce((acc, key) => (acc && acc[key] !== undefined ? acc[key] : null), dictionary[currentLang]);
}

function textOr(key, fallback) {
  const value = t(key);
  return typeof value === "string" ? value : fallback;
}

function applyTranslations() {
  document.documentElement.lang = currentLang;
  document.documentElement.dataset.lang = currentLang;
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    const key = node.dataset.i18n;
    const value = t(key);
    if (typeof value === "string") {
      node.textContent = value;
    }
  });
  const enBtn = document.getElementById("lang-en");
  const esBtn = document.getElementById("lang-es");
  if (enBtn && esBtn) {
    enBtn.classList.remove("bg-brand-700", "text-white");
    esBtn.classList.remove("bg-brand-700", "text-white");
    if (currentLang === "en") {
      enBtn.classList.add("bg-brand-700", "text-white");
      enBtn.setAttribute("aria-pressed", "true");
      esBtn.setAttribute("aria-pressed", "false");
    } else {
      esBtn.classList.add("bg-brand-700", "text-white");
      enBtn.setAttribute("aria-pressed", "false");
      esBtn.setAttribute("aria-pressed", "true");
    }
  }
  if (window.location.pathname.endsWith("signup.html")) {
    document.title = t("pageTitle.signup");
  } else if (window.location.pathname.endsWith("locations.html")) {
    document.title = t("pageTitle.locations");
  } else {
    document.title = t("pageTitle.index");
  }

  refreshSignupSelectText();
}

function setLanguage(lang) {
  currentLang = lang;
  localStorage.setItem("brasaland-lang", lang);
  applyTranslations();
}

function setupLanguageButtons() {
  const enBtn = document.getElementById("lang-en");
  const esBtn = document.getElementById("lang-es");
  if (enBtn) {
    enBtn.addEventListener("click", () => setLanguage("en"));
  }
  if (esBtn) {
    esBtn.addEventListener("click", () => setLanguage("es"));
  }
}

function getValidationMessages() {
  if (currentLang === "es") {
    return {
      required: "Este campo es obligatorio.",
      fullName: "Ingresa tu nombre completo (nombre y apellido).",
      email: "Ingresa un correo valido (ejemplo: nombre@email.com).",
      phone: "El telefono debe incluir codigo de pais (ejemplo: +57 300 123 4567 o +1 305 123 4567).",
      country: "Selecciona tu pais.",
      city: "Selecciona tu ciudad.",
      howFound: "Dinos como encontraste Brasaland.",
      dob: "Debes tener 18 anos o mas para registrarte en Brasa Points.",
      dobFuture: "La fecha de nacimiento no puede estar en el futuro.",
      terms: "Debes aceptar los terminos del programa Brasa Points para continuar.",
      formError: "Corrige los campos marcados y vuelve a enviar.",
      formSuccess:
        "Bienvenido a Brasa Points! Tu registro fue exitoso. Recibiras un correo de confirmacion en los proximos minutos con los detalles de tu cuenta y como empezar a ganar puntos. Ya puedes disfrutar tus beneficios en cualquiera de nuestras 14 sedes!",
    };
  }
  return {
    required: "This field is required.",
    fullName: "Enter your full name (first and last name).",
    email: "Enter a valid email (example: name@email.com).",
    phone: "Phone must include country code (example: +57 300 123 4567 or +1 305 123 4567).",
    country: "Select your country.",
    city: "Select your city.",
    howFound: "Tell us how you found Brasaland.",
    dob: "You must be 18 or older to register for Brasa Points.",
    dobFuture: "Date of birth cannot be in the future.",
    terms: "You must accept the Brasa Points program terms to continue.",
    formError: "Please correct the highlighted fields and submit again.",
    formSuccess:
      "Welcome to Brasa Points! Your registration was successful. You will receive a confirmation email in the next few minutes with your account details and how to start earning points. You can now enjoy your benefits at any of our 14 locations!",
  };
}

const cityOptionsByCountry = {
  Colombia: ["Medellin", "Bogota", "Cali"],
  "United States": ["Miami", "Orlando"],
};

const locationOptionsByCity = {
  Medellin: ["Brasaland El Poblado", "Brasaland Laureles", "Brasaland Envigado", "Brasaland Sabaneta"],
  Bogota: ["Brasaland Usaquen", "Brasaland Chapinero", "Brasaland Zona Rosa"],
  Cali: ["Brasaland Granada", "Brasaland Ciudad Jardin", "Brasaland Unicentro"],
  Miami: ["Brasaland Brickell", "Brasaland Coral Gables"],
  Orlando: ["Brasaland Downtown", "Brasaland International Drive"],
};

function setSelectOptions(selectNode, options, placeholder, selectedValue = "") {
  if (!selectNode) return;
  selectNode.innerHTML = "";
  const emptyOption = document.createElement("option");
  emptyOption.value = "";
  emptyOption.textContent = placeholder;
  selectNode.appendChild(emptyOption);

  options.forEach((option) => {
    const opt = document.createElement("option");
    if (typeof option === "string") {
      opt.value = option;
      opt.textContent = option;
    } else {
      opt.value = option.value;
      opt.textContent = option.label;
    }
    if (opt.value === selectedValue) {
      opt.selected = true;
    }
    selectNode.appendChild(opt);
  });
}

function updateDependentSelects(countryNode, cityNode, locationNode, keepSelections = false) {
  const selectedCountry = countryNode.value;
  const selectedCity = keepSelections ? cityNode.value : "";
  const selectedLocation = keepSelections ? locationNode.value : "";
  const cities = cityOptionsByCountry[selectedCountry] || [];
  setSelectOptions(cityNode, cities, textOr("form.selectCity", "Select your city"), selectedCity);

  const activeCity = cityNode.value;
  const locations = locationOptionsByCity[activeCity] || [];
  setSelectOptions(
    locationNode,
    locations,
    textOr("form.selectFavoriteLocation", "Select your favorite location (optional)"),
    selectedLocation,
  );
}

function updateLocationsForCity(cityNode, locationNode, keepSelection = false) {
  const selectedCity = cityNode.value;
  const selectedLocation = keepSelection ? locationNode.value : "";
  const locations = locationOptionsByCity[selectedCity] || [];
  setSelectOptions(
    locationNode,
    locations,
    textOr("form.selectFavoriteLocation", "Select your favorite location (optional)"),
    selectedLocation,
  );
}

function setFieldError(input, message) {
  const errorNode = document.getElementById(`error-${input.id}`);
  if (errorNode) {
    errorNode.textContent = message;
  }

  if (message) {
    input.setAttribute("aria-invalid", "true");
    input.classList.add("border-red-700", "ring-red-300");
  } else {
    input.setAttribute("aria-invalid", "false");
    input.classList.remove("border-red-700", "ring-red-300");
  }
}

function validateInput(input, messages) {
  const value = input.type === "checkbox" ? input.checked : input.value.trim();

  if (input.id === "acceptTerms") {
    if (!value) {
      setFieldError(input, messages.terms);
      return false;
    }
    setFieldError(input, "");
    return true;
  }

  if (!value) {
    if (input.id === "country") {
      setFieldError(input, messages.country);
    } else if (input.id === "city") {
      setFieldError(input, messages.city);
    } else if (input.id === "howFound") {
      setFieldError(input, messages.howFound);
    } else if (input.id === "dob") {
      setFieldError(input, messages.dob);
    } else {
      setFieldError(input, messages.required);
    }
    return false;
  }

  if (input.id === "fullName") {
    const wordCount = value.split(/\s+/).filter(Boolean).length;
    if (wordCount < 2) {
      setFieldError(input, messages.fullName);
      return false;
    }
  }

  if (input.id === "email") {
    const emailOk = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
    if (!emailOk) {
      setFieldError(input, messages.email);
      return false;
    }
  }

  if (input.id === "phone") {
    const normalized = value.replace(/[\s-]+/g, " ").trim();
    const phoneOk = /^\+(57|1)\s\d[\d\s-]{6,}$/.test(normalized);
    if (!phoneOk) {
      setFieldError(input, messages.phone);
      return false;
    }
  }

  if (input.id === "country" && !cityOptionsByCountry[value]) {
    setFieldError(input, messages.country);
    return false;
  }

  if (input.id === "city") {
    const countryNode = document.getElementById("country");
    const validCities = cityOptionsByCountry[countryNode ? countryNode.value : ""] || [];
    if (!validCities.includes(value)) {
      setFieldError(input, messages.city);
      return false;
    }
  }

  if (input.id === "dob") {
    const selected = new Date(value);
    if (Number.isNaN(selected.getTime())) {
      setFieldError(input, messages.dob);
      return false;
    }

    const today = new Date();
    today.setHours(0, 0, 0, 0);
    if (selected > today) {
      setFieldError(input, messages.dobFuture);
      return false;
    }

    let age = today.getFullYear() - selected.getFullYear();
    const monthDiff = today.getMonth() - selected.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < selected.getDate())) {
      age -= 1;
    }

    if (age < 18) {
      setFieldError(input, messages.dob);
      return false;
    }
  }

  setFieldError(input, "");
  return true;
}

function resetFormState({ form, inputs, statusNode, countryNode, cityNode, locationNode }) {
  form.reset();
  setSelectOptions(cityNode, [], textOr("form.selectCity", "Select your city"));
  setSelectOptions(locationNode, [], textOr("form.selectFavoriteLocation", "Select your favorite location (optional)"));
  inputs.forEach((input) => setFieldError(input, ""));
  statusNode.textContent = "";
  statusNode.classList.add("hidden");
  statusNode.classList.remove("border-red-300", "bg-red-50", "text-red-900", "border-green-300", "bg-green-50", "text-green-900");
}

function refreshSignupSelectText() {
  const form = document.getElementById("brasa-form");
  const countryNode = document.getElementById("country");
  const cityNode = document.getElementById("city");
  const locationNode = document.getElementById("favoriteLocation");
  if (!form || !countryNode || !cityNode || !locationNode) return;

  const selectedCountry = countryNode.value;
  const selectedCity = cityNode.value;
  const selectedLocation = locationNode.value;

  const countryPlaceholder = countryNode.querySelector('option[value=""]');
  if (countryPlaceholder) {
    countryPlaceholder.textContent = textOr("form.selectCountry", "Select your country");
  }

  const countryColombia = countryNode.querySelector('option[value="Colombia"]');
  if (countryColombia) {
    countryColombia.textContent = "Colombia";
  }

  const countryUS = countryNode.querySelector('option[value="United States"]');
  if (countryUS) {
    countryUS.textContent = currentLang === "es" ? "Estados Unidos" : "United States";
  }

  updateDependentSelects(countryNode, cityNode, locationNode, true);

  if (selectedCountry && countryNode.value !== selectedCountry) {
    countryNode.value = selectedCountry;
  }
  if (selectedCity && cityNode.querySelector(`option[value="${selectedCity}"]`)) {
    cityNode.value = selectedCity;
  }
  if (selectedLocation && locationNode.querySelector(`option[value="${selectedLocation}"]`)) {
    locationNode.value = selectedLocation;
  }
}

function setupSignupForm() {
  const form = document.getElementById("brasa-form");
  const statusNode = document.getElementById("form-status");
  if (!form || !statusNode) return;

  const countryNode = document.getElementById("country");
  const cityNode = document.getElementById("city");
  const locationNode = document.getElementById("favoriteLocation");
  const clearButton = document.getElementById("clear-form");

  const inputs = ["fullName", "email", "phone", "country", "city", "howFound", "dob", "acceptTerms"]
    .map((id) => document.getElementById(id))
    .filter(Boolean);

  if (countryNode && cityNode && locationNode) {
    updateDependentSelects(countryNode, cityNode, locationNode);
    countryNode.addEventListener("change", () => {
      updateDependentSelects(countryNode, cityNode, locationNode);
      validateInput(countryNode, getValidationMessages());
      setFieldError(cityNode, "");
    });
    cityNode.addEventListener("change", () => {
      updateLocationsForCity(cityNode, locationNode);
      validateInput(cityNode, getValidationMessages());
    });
  }

  inputs.forEach((input) => {
    input.setAttribute("aria-invalid", "false");
    const eventType = input.type === "checkbox" || input.tagName === "SELECT" ? "change" : "blur";
    input.addEventListener(eventType, () => validateInput(input, getValidationMessages()));
    if (input.tagName !== "SELECT" && input.type !== "checkbox") {
      input.addEventListener("input", () => {
        if (input.getAttribute("aria-invalid") === "true") {
          validateInput(input, getValidationMessages());
        }
      });
    }
  });

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const messages = getValidationMessages();
    let firstInvalid = null;

    const allValid = inputs.every((input) => {
      const valid = validateInput(input, messages);
      if (!valid && !firstInvalid) {
        firstInvalid = input;
      }
      return valid;
    });

    if (!allValid) {
      setFormStatus(statusNode, messages.formError, true);
      if (firstInvalid) {
        firstInvalid.focus();
      }
      return;
    }

    setFormStatus(statusNode, messages.formSuccess, false);
  });

  if (clearButton) {
    clearButton.addEventListener("click", () => {
      resetFormState({ form, inputs, statusNode, countryNode, cityNode, locationNode });
      const fullNameNode = document.getElementById("fullName");
      if (fullNameNode) {
        fullNameNode.focus();
      }
    });
  }
}

function setFormStatus(statusNode, message, hasError) {
  statusNode.textContent = message;
  statusNode.classList.remove("hidden", "border-red-300", "bg-red-50", "text-red-900", "border-green-300", "bg-green-50", "text-green-900");
  if (hasError) {
    statusNode.classList.add("border-red-300", "bg-red-50", "text-red-900");
    statusNode.setAttribute("role", "alert");
    statusNode.setAttribute("aria-live", "assertive");
  } else {
    statusNode.classList.add("border-green-300", "bg-green-50", "text-green-900");
    statusNode.setAttribute("role", "status");
    statusNode.setAttribute("aria-live", "polite");
  }
}


document.addEventListener("DOMContentLoaded", () => {
  setupLanguageButtons();
  applyTranslations();
  setupSignupForm();
});
