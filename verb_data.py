# format : (conjusoited_form, infinitive, mood, tense, person)

DATA = [
    # abréger - indicatif présent
    ("abrège", "abréger", "indicatif", "présent", "je"), ("abrèges", "abréger", "indicatif", "présent", "tu"), ("abrège", "abréger", "indicatif", "présent", "il/elle/on"),
    ("abrégeons", "abréger", "indicatif", "présent", "nous"), ("abrégez", "abréger", "indicatif", "présent", "vous"), ("abrègent", "abréger", "indicatif", "présent", "ils/elles"),
    # abréger - indicatif imparfait
    ("abrégeais", "abréger", "indicatif", "imparfait", "je"), ("abrégeais", "abréger", "indicatif", "imparfait", "tu"), ("abrégeait", "abréger", "indicatif", "imparfait", "il/elle/on"),
    ("abrégions", "abréger", "indicatif", "imparfait", "nous"), ("abrégiez", "abréger", "indicatif", "imparfait", "vous"), ("abrégeaient", "abréger", "indicatif", "imparfait", "ils/elles"),
    # abréger - indicatif passé simple
    ("abrégeai", "abréger", "indicatif", "passé simple", "je"), ("abrégeas", "abréger", "indicatif", "passé simple", "tu"), ("abrégea", "abréger", "indicatif", "passé simple", "il/elle/on"),
    ("abrégeâmes", "abréger", "indicatif", "passé simple", "nous"), ("abrégeâtes", "abréger", "indicatif", "passé simple", "vous"), ("abrégèrent", "abréger", "indicatif", "passé simple", "ils/elles"),
    # abréger - indicatif futur simple
    ("abrégerai", "abréger", "indicatif", "futur simple", "je"), ("abrégeras", "abréger", "indicatif", "futur simple", "tu"), ("abrégera", "abréger", "indicatif", "futur simple", "il/elle/on"),
    ("abrégerons", "abréger", "indicatif", "futur simple", "nous"), ("abrégerez", "abréger", "indicatif", "futur simple", "vous"), ("abrégeront", "abréger", "indicatif", "futur simple", "ils/elles"),
    # abréger - passé composé
    ("ai abrégé", "abréger", "indicatif", "passé composé", "je"), ("as abrégé", "abréger", "indicatif", "passé composé", "tu"), ("a abrégé", "abréger", "indicatif", "passé composé", "il/elle/on"),
    ("avons abrégé", "abréger", "indicatif", "passé composé", "nous"), ("avez abrégé", "abréger", "indicatif", "passé composé", "vous"), ("ont abrégé", "abréger", "indicatif", "passé composé", "ils/elles"),
    # abréger - plus-que-parfait
    ("avais abrégé", "abréger", "indicatif", "plus-que-parfait", "je"), ("avais abrégé", "abréger", "indicatif", "plus-que-parfait", "tu"), ("avait abrégé", "abréger", "indicatif", "plus-que-parfait", "il/elle/on"),
    ("avions abrégé", "abréger", "indicatif", "plus-que-parfait", "nous"), ("aviez abrégé", "abréger", "indicatif", "plus-que-parfait", "vous"), ("avaient abrégé", "abréger", "indicatif", "plus-que-parfait", "ils/elles"),
    # abréger - passé antérieur
    ("eus abrégé", "abréger", "indicatif", "passé antérieur", "je"), ("eus abrégé", "abréger", "indicatif", "passé antérieur", "tu"), ("eut abrégé", "abréger", "indicatif", "passé antérieur", "il/elle/on"),
    ("eûmes abrégé", "abréger", "indicatif", "passé antérieur", "nous"), ("eûtes abrégé", "abréger", "indicatif", "passé antérieur", "vous"), ("eurent abrégé", "abréger", "indicatif", "passé antérieur", "ils/elles"),
    # abréger - futur antérieur
    ("aurai abrégé", "abréger", "indicatif", "futur antérieur", "je"), ("auras abrégé", "abréger", "indicatif", "futur antérieur", "tu"), ("aura abrégé", "abréger", "indicatif", "futur antérieur", "il/elle/on"),
    ("aurons abrégé", "abréger", "indicatif", "futur antérieur", "nous"), ("aurez abrégé", "abréger", "indicatif", "futur antérieur", "vous"), ("auront abrégé", "abréger", "indicatif", "futur antérieur", "ils/elles"),
    # abréger - conditionnel présent
    ("abrégerais", "abréger", "conditionnel", "présent", "je"), ("abrégerais", "abréger", "conditionnel", "présent", "tu"), ("abrégerait", "abréger", "conditionnel", "présent", "il/elle/on"),
    ("abrégerions", "abréger", "conditionnel", "présent", "nous"), ("abrégeriez", "abréger", "conditionnel", "présent", "vous"), ("abrégeraient", "abréger", "conditionnel", "présent", "ils/elles"),
    # abréger - conditionnel passé
    ("aurais abrégé", "abréger", "conditionnel", "passé", "je"), ("aurais abrégé", "abréger", "conditionnel", "passé", "tu"), ("aurait abrégé", "abréger", "conditionnel", "passé", "il/elle/on"),
    ("aurions abrégé", "abréger", "conditionnel", "passé", "nous"), ("auriez abrégé", "abréger", "conditionnel", "passé", "vous"), ("auraient abrégé", "abréger", "conditionnel", "passé", "ils/elles"),
    # abréger - subjonctif présent
    ("abrège", "abréger", "subjonctif", "présent", "je"), ("abrèges", "abréger", "subjonctif", "présent", "tu"), ("abrège", "abréger", "subjonctif", "présent", "il/elle/on"),
    ("abrégions", "abréger", "subjonctif", "présent", "nous"), ("abrégiez", "abréger", "subjonctif", "présent", "vous"), ("abrègent", "abréger", "subjonctif", "présent", "ils/elles"),
    # abréger - subjonctif passé
    ("aie abrégé", "abréger", "subjonctif", "passé", "je"), ("aies abrégé", "abréger", "subjonctif", "passé", "tu"), ("ait abrégé", "abréger", "subjonctif", "passé", "il/elle/on"),
    ("ayons abrégé", "abréger", "subjonctif", "passé", "nous"), ("ayez abrégé", "abréger", "subjonctif", "passé", "vous"), ("aient abrégé", "abréger", "subjonctif", "passé", "ils/elles"),
    # abréger - subjonctif imparfait
    ("abrégeasse", "abréger", "subjonctif", "imparfait", "je"), ("abrégeasses", "abréger", "subjonctif", "imparfait", "tu"), ("abrégeât", "abréger", "subjonctif", "imparfait", "il/elle/on"),
    ("abrégeassions", "abréger", "subjonctif", "imparfait", "nous"), ("abrégeassiez", "abréger", "subjonctif", "imparfait", "vous"), ("abrégeassent", "abréger", "subjonctif", "imparfait", "ils/elles"),
    # abréger - subjonctif plus-que-parfait
    ("eusse abrégé", "abréger", "subjonctif", "plus-que-parfait", "je"), ("eusses abrégé", "abréger", "subjonctif", "plus-que-parfait", "tu"), ("eût abrégé", "abréger", "subjonctif", "plus-que-parfait", "il/elle/on"),
    ("eussions abrégé", "abréger", "subjonctif", "plus-que-parfait", "nous"), ("eussiez abrégé", "abréger", "subjonctif", "plus-que-parfait", "vous"), ("eussent abrégé", "abréger", "subjonctif", "plus-que-parfait", "ils/elles"),
    # abréger - impératif présent
    ("abrège", "abréger", "impératif", "présent", "tu"), ("abrégeons", "abréger", "impératif", "présent", "nous"), ("abrégez", "abréger", "impératif", "présent", "vous"),
    # abréger - impératif passé
    ("aie abrégé", "abréger", "impératif", "passé", "tu"), ("ayons abrégé", "abréger", "impératif", "passé", "nous"), ("ayez abrégé", "abréger", "impératif", "passé", "vous"),
    # abréger - infinitif présent
    ("abréger", "abréger", "infinitif", "présent", "n/a"),
    # abréger - infinitif passé
    ("avoir abrégé", "abréger", "infinitif", "passé", "n/a"),
    # abréger - participe présent
    ("abrégeant", "abréger", "participe", "présent", "n/a"),
    # abréger - participe passé
    ("abrégé", "abréger", "participe", "passé", "n/a"),
    ("abrégée", "abréger", "participe", "passé", "n/a"),
    ("abrégés", "abréger", "participe", "passé", "n/a"),
    ("abrégées", "abréger", "participe", "passé", "n/a"),

    # désagréger - indicatif présent
    ("désagrège", "désagréger", "indicatif", "présent", "je"), ("désagrèges", "désagréger", "indicatif", "présent", "tu"), ("désagrège", "désagréger", "indicatif", "présent", "il/elle/on"),
    ("désagrégeons", "désagréger", "indicatif", "présent", "nous"), ("désagrégez", "désagréger", "indicatif", "présent", "vous"), ("désagrègent", "désagréger", "indicatif", "présent", "ils/elles"),
    # désagréger - indicatif imparfait
    ("désagrégeais", "désagréger", "indicatif", "imparfait", "je"), ("désagrégeais", "désagréger", "indicatif", "imparfait", "tu"), ("désagrégeait", "désagréger", "indicatif", "imparfait", "il/elle/on"),
    ("désagrégions", "désagréger", "indicatif", "imparfait", "nous"), ("désagrégiez", "désagréger", "indicatif", "imparfait", "vous"), ("désagrégeaient", "désagréger", "indicatif", "imparfait", "ils/elles"),
    # désagréger - indicatif passé simple
    ("désagrégeai", "désagréger", "indicatif", "passé simple", "je"), ("désagrégeas", "désagréger", "indicatif", "passé simple", "tu"), ("désagrégea", "désagréger", "indicatif", "passé simple", "il/elle/on"),
    ("désagrégeâmes", "désagréger", "indicatif", "passé simple", "nous"), ("désagrégeâtes", "désagréger", "indicatif", "passé simple", "vous"), ("désagrégèrent", "désagréger", "indicatif", "passé simple", "ils/elles"),
    # désagréger - indicatif futur simple
    ("désagrégerai", "désagréger", "indicatif", "futur simple", "je"), ("désagrégeras", "désagréger", "indicatif", "futur simple", "tu"), ("désagrégera", "désagréger", "indicatif", "futur simple", "il/elle/on"),
    ("désagrégerons", "désagréger", "indicatif", "futur simple", "nous"), ("désagrégerez", "désagréger", "indicatif", "futur simple", "vous"), ("désagrégeront", "désagréger", "indicatif", "futur simple", "ils/elles"),
    # désagréger - passé composé
    ("ai désagrégé", "désagréger", "indicatif", "passé composé", "je"), ("as désagrégé", "désagréger", "indicatif", "passé composé", "tu"), ("a désagrégé", "désagréger", "indicatif", "passé composé", "il/elle/on"),
    ("avons désagrégé", "désagréger", "indicatif", "passé composé", "nous"), ("avez désagrégé", "désagréger", "indicatif", "passé composé", "vous"), ("ont désagrégé", "désagréger", "indicatif", "passé composé", "ils/elles"),
    # désagréger - plus-que-parfait
    ("avais désagrégé", "désagréger", "indicatif", "plus-que-parfait", "je"), ("avais désagrégé", "désagréger", "indicatif", "plus-que-parfait", "tu"), ("avait désagrégé", "désagréger", "indicatif", "plus-que-parfait", "il/elle/on"),
    ("avions désagrégé", "désagréger", "indicatif", "plus-que-parfait", "nous"), ("aviez désagrégé", "désagréger", "indicatif", "plus-que-parfait", "vous"), ("avaient désagrégé", "désagréger", "indicatif", "plus-que-parfait", "ils/elles"),
    # désagréger - passé antérieur
    ("eus désagrégé", "désagréger", "indicatif", "passé antérieur", "je"), ("eus désagrégé", "désagréger", "indicatif", "passé antérieur", "tu"), ("eut désagrégé", "désagréger", "indicatif", "passé antérieur", "il/elle/on"),
    ("eûmes désagrégé", "désagréger", "indicatif", "passé antérieur", "nous"), ("eûtes désagrégé", "désagréger", "indicatif", "passé antérieur", "vous"), ("eurent désagrégé", "désagréger", "indicatif", "passé antérieur", "ils/elles"),
    # désagréger - futur antérieur
    ("aurai désagrégé", "désagréger", "indicatif", "futur antérieur", "je"), ("auras désagrégé", "désagréger", "indicatif", "futur antérieur", "tu"), ("aura désagrégé", "désagréger", "indicatif", "futur antérieur", "il/elle/on"),
    ("aurons désagrégé", "désagréger", "indicatif", "futur antérieur", "nous"), ("aurez désagrégé", "désagréger", "indicatif", "futur antérieur", "vous"), ("auront désagrégé", "désagréger", "indicatif", "futur antérieur", "ils/elles"),
    # désagréger - conditionnel présent
    ("désagrégerais", "désagréger", "conditionnel", "présent", "je"), ("désagrégerais", "désagréger", "conditionnel", "présent", "tu"), ("désagrégerait", "désagréger", "conditionnel", "présent", "il/elle/on"),
    ("désagrégerions", "désagréger", "conditionnel", "présent", "nous"), ("désagrégeriez", "désagréger", "conditionnel", "présent", "vous"), ("désagrégeraient", "désagréger", "conditionnel", "présent", "ils/elles"),
    # désagréger - conditionnel passé
    ("aurais désagrégé", "désagréger", "conditionnel", "passé", "je"), ("aurais désagrégé", "désagréger", "conditionnel", "passé", "tu"), ("aurait désagrégé", "désagréger", "conditionnel", "passé", "il/elle/on"),
    ("aurions désagrégé", "désagréger", "conditionnel", "passé", "nous"), ("auriez désagrégé", "désagréger", "conditionnel", "passé", "vous"), ("auraient désagrégé", "désagréger", "conditionnel", "passé", "ils/elles"),
    # désagréger - subjonctif présent
    ("désagrège", "désagréger", "subjonctif", "présent", "je"), ("désagrèges", "désagréger", "subjonctif", "présent", "tu"), ("désagrège", "désagréger", "subjonctif", "présent", "il/elle/on"),
    ("désagrégions", "désagréger", "subjonctif", "présent", "nous"), ("désagrégiez", "désagréger", "subjonctif", "présent", "vous"), ("désagrègent", "désagréger", "subjonctif", "présent", "ils/elles"),
    # désagréger - subjonctif passé
    ("aie désagrégé", "désagréger", "subjonctif", "passé", "je"), ("aies désagrégé", "désagréger", "subjonctif", "passé", "tu"), ("ait désagrégé", "désagréger", "subjonctif", "passé", "il/elle/on"),
    ("ayons désagrégé", "désagréger", "subjonctif", "passé", "nous"), ("ayez désagrégé", "désagréger", "subjonctif", "passé", "vous"), ("aient désagrégé", "désagréger", "subjonctif", "passé", "ils/elles"),
    # désagréger - subjonctif imparfait
    ("désagrégeasse", "désagréger", "subjonctif", "imparfait", "je"), ("désagrégeasses", "désagréger", "subjonctif", "imparfait", "tu"), ("désagrégeât", "désagréger", "subjonctif", "imparfait", "il/elle/on"),
    ("désagrégeassions", "désagréger", "subjonctif", "imparfait", "nous"), ("désagrégeassiez", "désagréger", "subjonctif", "imparfait", "vous"), ("désagrégeassent", "désagréger", "subjonctif", "imparfait", "ils/elles"),
    # désagréger - subjonctif plus-que-parfait
    ("eusse désagrégé", "désagréger", "subjonctif", "plus-que-parfait", "je"), ("eusses désagrégé", "désagréger", "subjonctif", "plus-que-parfait", "tu"), ("eût désagrégé", "désagréger", "subjonctif", "plus-que-parfait", "il/elle/on"),
    ("eussions désagrégé", "désagréger", "subjonctif", "plus-que-parfait", "nous"), ("eussiez désagrégé", "désagréger", "subjonctif", "plus-que-parfait", "vous"), ("eussent désagrégé", "désagréger", "subjonctif", "plus-que-parfait", "ils/elles"),
    # désagréger - impératif présent
    ("désagrège", "désagréger", "impératif", "présent", "tu"), ("désagrégeons", "désagréger", "impératif", "présent", "nous"), ("désagrégez", "désagréger", "impératif", "présent", "vous"),
    # désagréger - impératif passé
    ("aie désagrégé", "désagréger", "impératif", "passé", "tu"), ("ayons désagrégé", "désagréger", "impératif", "passé", "nous"), ("ayez désagrégé", "désagréger", "impératif", "passé", "vous"),
    # désagréger - infinitif présent
    ("désagréger", "désagréger", "infinitif", "présent", "n/a"),
    # désagréger - infinitif passé
    ("avoir désagrégé", "désagréger", "infinitif", "passé", "n/a"),
    # désagréger - participe présent
    ("désagrégeant", "désagréger", "participe", "présent", "n/a"),
    # désagréger - participe passé
    ("désagrégé", "désagréger", "participe", "passé", "n/a"),
    ("désagrégée", "désagréger", "participe", "passé", "n/a"),
    ("désagrégés", "désagréger", "participe", "passé", "n/a"),
    ("désagrégées", "désagréger", "participe", "passé", "n/a"),

    # piéger - indicatif présent
    ("piège", "piéger", "indicatif", "présent", "je"), ("pièges", "piéger", "indicatif", "présent", "tu"), ("piège", "piéger", "indicatif", "présent", "il/elle/on"),
    ("piégeons", "piéger", "indicatif", "présent", "nous"), ("piégez", "piéger", "indicatif", "présent", "vous"), ("piègent", "piéger", "indicatif", "présent", "ils/elles"),
    # piéger - indicatif imparfait
    ("piégeais", "piéger", "indicatif", "imparfait", "je"), ("piégeais", "piéger", "indicatif", "imparfait", "tu"), ("piégeait", "piéger", "indicatif", "imparfait", "il/elle/on"),
    ("piégions", "piéger", "indicatif", "imparfait", "nous"), ("piégiez", "piéger", "indicatif", "imparfait", "vous"), ("piégeaient", "piéger", "indicatif", "imparfait", "ils/elles"),
    # piéger - indicatif passé simple
    ("piégeai", "piéger", "indicatif", "passé simple", "je"), ("piégeas", "piéger", "indicatif", "passé simple", "tu"), ("piégea", "piéger", "indicatif", "passé simple", "il/elle/on"),
    ("piégeâmes", "piéger", "indicatif", "passé simple", "nous"), ("piégeâtes", "piéger", "indicatif", "passé simple", "vous"), ("piégèrent", "piéger", "indicatif", "passé simple", "ils/elles"),
    # piéger - indicatif futur simple
    ("piégerai", "piéger", "indicatif", "futur simple", "je"), ("piégeras", "piéger", "indicatif", "futur simple", "tu"), ("piégera", "piéger", "indicatif", "futur simple", "il/elle/on"),
    ("piégerons", "piéger", "indicatif", "futur simple", "nous"), ("piégerez", "piéger", "indicatif", "futur simple", "vous"), ("piégeront", "piéger", "indicatif", "futur simple", "ils/elles"),
    # piéger - passé composé
    ("ai piégé", "piéger", "indicatif", "passé composé", "je"), ("as piégé", "piéger", "indicatif", "passé composé", "tu"), ("a piégé", "piéger", "indicatif", "passé composé", "il/elle/on"),
    ("avons piégé", "piéger", "indicatif", "passé composé", "nous"), ("avez piégé", "piéger", "indicatif", "passé composé", "vous"), ("ont piégé", "piéger", "indicatif", "passé composé", "ils/elles"),
    # piéger - plus-que-parfait
    ("avais piégé", "piéger", "indicatif", "plus-que-parfait", "je"), ("avais piégé", "piéger", "indicatif", "plus-que-parfait", "tu"), ("avait piégé", "piéger", "indicatif", "plus-que-parfait", "il/elle/on"),
    ("avions piégé", "piéger", "indicatif", "plus-que-parfait", "nous"), ("aviez piégé", "piéger", "indicatif", "plus-que-parfait", "vous"), ("avaient piégé", "piéger", "indicatif", "plus-que-parfait", "ils/elles"),
    # piéger - passé antérieur
    ("eus piégé", "piéger", "indicatif", "passé antérieur", "je"), ("eus piégé", "piéger", "indicatif", "passé antérieur", "tu"), ("eut piégé", "piéger", "indicatif", "passé antérieur", "il/elle/on"),
    ("eûmes piégé", "piéger", "indicatif", "passé antérieur", "nous"), ("eûtes piégé", "piéger", "indicatif", "passé antérieur", "vous"), ("eurent piégé", "piéger", "indicatif", "passé antérieur", "ils/elles"),
    # piéger - futur antérieur
    ("aurai piégé", "piéger", "indicatif", "futur antérieur", "je"), ("auras piégé", "piéger", "indicatif", "futur antérieur", "tu"), ("aura piégé", "piéger", "indicatif", "futur antérieur", "il/elle/on"),
    ("aurons piégé", "piéger", "indicatif", "futur antérieur", "nous"), ("aurez piégé", "piéger", "indicatif", "futur antérieur", "vous"), ("auront piégé", "piéger", "indicatif", "futur antérieur", "ils/elles"),
    # piéger - conditionnel présent
    ("piégerais", "piéger", "conditionnel", "présent", "je"), ("piégerais", "piéger", "conditionnel", "présent", "tu"), ("piégerait", "piéger", "conditionnel", "présent", "il/elle/on"),
    ("piégerions", "piéger", "conditionnel", "présent", "nous"), ("piégeriez", "piéger", "conditionnel", "présent", "vous"), ("piégeraient", "piéger", "conditionnel", "présent", "ils/elles"),
    # piéger - conditionnel passé
    ("aurais piégé", "piéger", "conditionnel", "passé", "je"), ("aurais piégé", "piéger", "conditionnel", "passé", "tu"), ("aurait piégé", "piéger", "conditionnel", "passé", "il/elle/on"),
    ("aurions piégé", "piéger", "conditionnel", "passé", "nous"), ("auriez piégé", "piéger", "conditionnel", "passé", "vous"), ("auraient piégé", "piéger", "conditionnel", "passé", "ils/elles"),
    # piéger - subjonctif présent
    ("piège", "piéger", "subjonctif", "présent", "je"), ("pièges", "piéger", "subjonctif", "présent", "tu"), ("piège", "piéger", "subjonctif", "présent", "il/elle/on"),
    ("piégions", "piéger", "subjonctif", "présent", "nous"), ("piégiez", "piéger", "subjonctif", "présent", "vous"), ("piègent", "piéger", "subjonctif", "présent", "ils/elles"),
    # piéger - subjonctif passé
    ("aie piégé", "piéger", "subjonctif", "passé", "je"), ("aies piégé", "piéger", "subjonctif", "passé", "tu"), ("ait piégé", "piéger", "subjonctif", "passé", "il/elle/on"),
    ("ayons piégé", "piéger", "subjonctif", "passé", "nous"), ("ayez piégé", "piéger", "subjonctif", "passé", "vous"), ("aient piégé", "piéger", "subjonctif", "passé", "ils/elles"),
    # piéger - subjonctif imparfait
    ("piégeasse", "piéger", "subjonctif", "imparfait", "je"), ("piégeasses", "piéger", "subjonctif", "imparfait", "tu"), ("piégeât", "piéger", "subjonctif", "imparfait", "il/elle/on"),
    ("piégeassions", "piéger", "subjonctif", "imparfait", "nous"), ("piégeassiez", "piéger", "subjonctif", "imparfait", "vous"), ("piégeassent", "piéger", "subjonctif", "imparfait", "ils/elles"),
    # piéger - subjonctif plus-que-parfait
    ("eusse piégé", "piéger", "subjonctif", "plus-que-parfait", "je"), ("eusses piégé", "piéger", "subjonctif", "plus-que-parfait", "tu"), ("eût piégé", "piéger", "subjonctif", "plus-que-parfait", "il/elle/on"),
    ("eussions piégé", "piéger", "subjonctif", "plus-que-parfait", "nous"), ("eussiez piégé", "piéger", "subjonctif", "plus-que-parfait", "vous"), ("eussent piégé", "piéger", "subjonctif", "plus-que-parfait", "ils/elles"),
    # piéger - impératif présent
    ("piège", "piéger", "impératif", "présent", "tu"), ("piégeons", "piéger", "impératif", "présent", "nous"), ("piégez", "piéger", "impératif", "présent", "vous"),
    # piéger - impératif passé
    ("aie piégé", "piéger", "impératif", "passé", "tu"), ("ayons piégé", "piéger", "impératif", "passé", "nous"), ("ayez piégé", "piéger", "impératif", "passé", "vous"),
    # piéger - infinitif présent
    ("piéger", "piéger", "infinitif", "présent", "n/a"),
    # piéger - infinitif passé
    ("avoir piégé", "piéger", "infinitif", "passé", "n/a"),
    # piéger - participe présent
    ("piégeant", "piéger", "participe", "présent", "n/a"),
    # piéger - participe passé
    ("piégé", "piéger", "participe", "passé", "n/a"),
    ("piégée", "piéger", "participe", "passé", "n/a"),
    ("piégés", "piéger", "participe", "passé", "n/a"),
    ("piégées", "piéger", "participe", "passé", "n/a"),

    # siéger - indicatif présent
    ("siège", "siéger", "indicatif", "présent", "je"), ("sièges", "siéger", "indicatif", "présent", "tu"), ("siège", "siéger", "indicatif", "présent", "il/elle/on"),
    ("siégeons", "siéger", "indicatif", "présent", "nous"), ("siégez", "siéger", "indicatif", "présent", "vous"), ("siègent", "siéger", "indicatif", "présent", "ils/elles"),
    # siéger - indicatif imparfait
    ("siégeais", "siéger", "indicatif", "imparfait", "je"), ("siégeais", "siéger", "indicatif", "imparfait", "tu"), ("siégeait", "siéger", "indicatif", "imparfait", "il/elle/on"),
    ("siégions", "siéger", "indicatif", "imparfait", "nous"), ("siégiez", "siéger", "indicatif", "imparfait", "vous"), ("siégeaient", "siéger", "indicatif", "imparfait", "ils/elles"),
    # siéger - indicatif passé simple
    ("siégeai", "siéger", "indicatif", "passé simple", "je"), ("siégeas", "siéger", "indicatif", "passé simple", "tu"), ("siégea", "siéger", "indicatif", "passé simple", "il/elle/on"),
    ("siégeâmes", "siéger", "indicatif", "passé simple", "nous"), ("siégeâtes", "siéger", "indicatif", "passé simple", "vous"), ("siégèrent", "siéger", "indicatif", "passé simple", "ils/elles"),
    # siéger - indicatif futur simple
    ("siégerai", "siéger", "indicatif", "futur simple", "je"), ("siégeras", "siéger", "indicatif", "futur simple", "tu"), ("siégera", "siéger", "indicatif", "futur simple", "il/elle/on"),
    ("siégerons", "siéger", "indicatif", "futur simple", "nous"), ("siégerez", "siéger", "indicatif", "futur simple", "vous"), ("siégeront", "siéger", "indicatif", "futur simple", "ils/elles"),
    # siéger - passé composé
    ("ai siégé", "siéger", "indicatif", "passé composé", "je"), ("as siégé", "siéger", "indicatif", "passé composé", "tu"), ("a siégé", "siéger", "indicatif", "passé composé", "il/elle/on"),
    ("avons siégé", "siéger", "indicatif", "passé composé", "nous"), ("avez siégé", "siéger", "indicatif", "passé composé", "vous"), ("ont siégé", "siéger", "indicatif", "passé composé", "ils/elles"),
    # siéger - plus-que-parfait
    ("avais siégé", "siéger", "indicatif", "plus-que-parfait", "je"), ("avais siégé", "siéger", "indicatif", "plus-que-parfait", "tu"), ("avait siégé", "siéger", "indicatif", "plus-que-parfait", "il/elle/on"),
    ("avions siégé", "siéger", "indicatif", "plus-que-parfait", "nous"), ("aviez siégé", "siéger", "indicatif", "plus-que-parfait", "vous"), ("avaient siégé", "siéger", "indicatif", "plus-que-parfait", "ils/elles"),
    # siéger - passé antérieur
    ("eus siégé", "siéger", "indicatif", "passé antérieur", "je"), ("eus siégé", "siéger", "indicatif", "passé antérieur", "tu"), ("eut siégé", "siéger", "indicatif", "passé antérieur", "il/elle/on"),
    ("eûmes siégé", "siéger", "indicatif", "passé antérieur", "nous"), ("eûtes siégé", "siéger", "indicatif", "passé antérieur", "vous"), ("eurent siégé", "siéger", "indicatif", "passé antérieur", "ils/elles"),
    # siéger - futur antérieur
    ("aurai siégé", "siéger", "indicatif", "futur antérieur", "je"), ("auras siégé", "siéger", "indicatif", "futur antérieur", "tu"), ("aura siégé", "siéger", "indicatif", "futur antérieur", "il/elle/on"),
    ("aurons siégé", "siéger", "indicatif", "futur antérieur", "nous"), ("aurez siégé", "siéger", "indicatif", "futur antérieur", "vous"), ("auront siégé", "siéger", "indicatif", "futur antérieur", "ils/elles"),
    # siéger - conditionnel présent
    ("siégerais", "siéger", "conditionnel", "présent", "je"), ("siégerais", "siéger", "conditionnel", "présent", "tu"), ("siégerait", "siéger", "conditionnel", "présent", "il/elle/on"),
    ("siégerions", "siéger", "conditionnel", "présent", "nous"), ("siégeriez", "siéger", "conditionnel", "présent", "vous"), ("siégeraient", "siéger", "conditionnel", "présent", "ils/elles"),
    # siéger - conditionnel passé
    ("aurais siégé", "siéger", "conditionnel", "passé", "je"), ("aurais siégé", "siéger", "conditionnel", "passé", "tu"), ("aurait siégé", "siéger", "conditionnel", "passé", "il/elle/on"),
    ("aurions siégé", "siéger", "conditionnel", "passé", "nous"), ("auriez siégé", "siéger", "conditionnel", "passé", "vous"), ("auraient siégé", "siéger", "conditionnel", "passé", "ils/elles"),
    # siéger - subjonctif présent
    ("siège", "siéger", "subjonctif", "présent", "je"), ("sièges", "siéger", "subjonctif", "présent", "tu"), ("siège", "siéger", "subjonctif", "présent", "il/elle/on"),
    ("siégions", "siéger", "subjonctif", "présent", "nous"), ("siégiez", "siéger", "subjonctif", "présent", "vous"), ("siègent", "siéger", "subjonctif", "présent", "ils/elles"),
    # siéger - subjonctif passé
    ("aie siégé", "siéger", "subjonctif", "passé", "je"), ("aies siégé", "siéger", "subjonctif", "passé", "tu"), ("ait siégé", "siéger", "subjonctif", "passé", "il/elle/on"),
    ("ayons siégé", "siéger", "subjonctif", "passé", "nous"), ("ayez siégé", "siéger", "subjonctif", "passé", "vous"), ("aient siégé", "siéger", "subjonctif", "passé", "ils/elles"),
    # siéger - subjonctif imparfait
    ("siégeasse", "siéger", "subjonctif", "imparfait", "je"), ("siégeasses", "siéger", "subjonctif", "imparfait", "tu"), ("siégeât", "siéger", "subjonctif", "imparfait", "il/elle/on"),
    ("siégeassions", "siéger", "subjonctif", "imparfait", "nous"), ("siégeassiez", "siéger", "subjonctif", "imparfait", "vous"), ("siégeassent", "siéger", "subjonctif", "imparfait", "ils/elles"),
    # siéger - subjonctif plus-que-parfait
    ("eusse siégé", "siéger", "subjonctif", "plus-que-parfait", "je"), ("eusses siégé", "siéger", "subjonctif", "plus-que-parfait", "tu"), ("eût siégé", "siéger", "subjonctif", "plus-que-parfait", "il/elle/on"),
    ("eussions siégé", "siéger", "subjonctif", "plus-que-parfait", "nous"), ("eussiez siégé", "siéger", "subjonctif", "plus-que-parfait", "vous"), ("eussent siégé", "siéger", "subjonctif", "plus-que-parfait", "ils/elles"),
    # siéger - impératif présent
    ("siège", "siéger", "impératif", "présent", "tu"), ("siégeons", "siéger", "impératif", "présent", "nous"), ("siégez", "siéger", "impératif", "présent", "vous"),
    # siéger - impératif passé
    ("aie siégé", "siéger", "impératif", "passé", "tu"), ("ayons siégé", "siéger", "impératif", "passé", "nous"), ("ayez siégé", "siéger", "impératif", "passé", "vous"),
    # siéger - infinitif présent
    ("siéger", "siéger", "infinitif", "présent", "n/a"),
    # siéger - infinitif passé
    ("avoir siégé", "siéger", "infinitif", "passé", "n/a"),
    # siéger - participe présent
    ("siégeant", "siéger", "participe", "présent", "n/a"),
    # siéger - participe passé
    ("siégé", "siéger", "participe", "passé", "n/a")
]