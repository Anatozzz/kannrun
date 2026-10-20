/*
 * Polyglotte — coordonnées du site, à compléter par le fondateur.
 *
 * C'est le SEUL fichier à modifier pour brancher le site : index.html et
 * mentions-legales.html lisent cet objet (attributs data-config="…") et
 * remplissent les liens au chargement.
 *
 * Règle : une valeur laissée vide ("") n'affiche rien de faux. Le lien
 * concerné est masqué ou renvoie vers le formulaire d'audit intégré.
 * N'inscrivez ici que des informations réelles.
 */
window.POLYGLOTTE = {
  // Adresse e-mail de contact. Sert au lien « Écrire un e-mail » et au
  // formulaire d'audit (qui compose un e-mail prérempli vers cette adresse).
  // Exemple de format : "bonjour@votre-domaine.fr"
  email: "",

  // Numéro de téléphone tel qu'il doit s'afficher. Les espaces sont gardés
  // à l'affichage et retirés dans le lien tel:. Format : "06 12 34 56 78"
  // ou "+33 6 12 34 56 78".
  telephone: "",

  // Numéro WhatsApp au format international, chiffres uniquement, sans le
  // « + » ni le 0 initial (ex. 33612345678). Produit un lien https://wa.me/…
  whatsapp: "",

  // Lien de prise de rendez-vous (Cal.com, Calendly…), adresse complète en
  // https://. Vide : le bouton « Prendre rendez-vous » est masqué.
  lienRdv: "",

  // Lien d'un formulaire externe (Tally…), adresse complète en https://.
  // Renseigné : le formulaire d'audit et les boutons y redirigent, avec les
  // champs déjà saisis passés en paramètres d'URL (préremplissage Tally si
  // les champs cachés portent les mêmes noms : restaurant, prenom,
  // telephone, email, quartier).
  // Vide : le formulaire intégré compose un e-mail vers `email`.
  lienFormulaire: "",

  // Numéro SIRET (14 chiffres), affiché dans les mentions légales.
  // À renseigner dès l'immatriculation, avant toute mise en ligne publique.
  siret: "",

  // Prénom et nom du responsable (éditeur du site, directeur de la
  // publication, responsable du traitement des données).
  nomResponsable: "",

  // Adresse affichée dans les mentions légales et le pied de page.
  // Un micro-entrepreneur doit indiquer son adresse professionnelle
  // (domicile ou domiciliation) dans les mentions légales.
  adresse: "Annecy (74)"
};
