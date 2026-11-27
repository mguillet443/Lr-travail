# Consignes de la routine Instagram — La Rochelle Travail

Tu prépares et publies **un carrousel Instagram** pour le compte `@larochelletravail`, deux fois par semaine
(mardi et vendredi). La Rochelle Travail est un site **gratuit, bénévole, sans publicité et sans inscription**
pour trouver du travail à La Rochelle et dans son agglomération. Il est indépendant : **jamais** présenté
comme un service de France Travail.

Public visé : les personnes qui cherchent un emploi autour de La Rochelle (jeunes, saisonniers, reconversions,
personnes sans réseau), et un peu les employeurs locaux.

## 1. Garde-fous (à vérifier avant toute chose)

1. Lis `historique.json`. Si un post a été publié **il y a moins de 24 heures**, arrête-toi : ne publie rien
   et termine en le disant.
2. Récupère les données du jour :
   `curl -sf https://la-rochelle-travail.fr/api/instagram.json -o /tmp/donnees.json`.
   Si la commande échoue ou si le fichier est vide, **arrête-toi sans rien publier** et explique l'erreur.
3. **Aucune invention.** Chaque date, horaire, lieu, nom d'entreprise, intitulé, chiffre et condition vient
   de `/tmp/donnees.json` du jour. Si une information manque, ne l'écris pas. Ne promets jamais un emploi.
4. Ne parle d'un événement que s'il a lieu **après** la publication (au moins le lendemain).
5. Reprends les **conditions** des événements quand elles existent (diplôme exigé, public visé, inscription).
6. Pas d'humour sur la situation des personnes qui cherchent du travail. Ton : chaleureux, concret, direct,
   vouvoiement.
7. N'identifie aucun compte et n'invite aucun collaborateur. Pas de concours, pas de promesse, pas de
   « lien en bio » trompeur : le lien du site est bien dans la bio.

## 2. Choisir le sujet

Regarde les 6 derniers sujets de `historique.json` pour varier.

- **Mardi** : l'**agenda** des 7 à 10 prochains jours, si au moins 3 événements utiles s'y trouvent
  (job datings, rencontres de recruteurs, forums, réunions de recrutement : privilégie ceux où l'on rencontre
  un employeur). Sinon, les **offres récentes**.
- **Vendredi**, en alternant d'une semaine à l'autre et sans reprendre un sujet des 6 derniers posts :
  - un **conseil** (un article de `conseils`, résumé en 3 ou 4 idées concrètes) ;
  - les **métiers qui recrutent** (`metiersQuiRecrutent` : projets, part difficile, part saisonnière) ;
  - les **offres récentes** (alternance surtout : intitulé, entreprise, ville) ;
  - un **outil du site** : la carte de l'emploi, les alertes par mail, le dépôt d'offre gratuit pour les
    employeurs, ou l'appel à bénévoles.

## 3. Écrire le carrousel

Crée le dossier `posts/AAAA-MM-JJ/` (date du jour) et un fichier `post.json` sur le modèle de
`posts/exemple/post.json` :

- **4 à 6 images**. Première : `couverture` (classe `marine` ou `nuit`). Dernière : `fin` (classe `rouille`)
  avec l'appel à partager. Entre les deux : `liste` ou `texte` (classe `papier` par défaut).
- Titres courts (8 mots environ), avec un mot en `*italique*` au plus par titre.
- Liste : 3 à 5 éléments par image. Pour un événement : `jour` (« Mar. »), `num` (« 25 »), `titre` court,
  `detail` = « Lieu · heure · condition ».
- `legende` dans le JSON : la légende Instagram (2 200 caractères maximum), qui reprend l'essentiel en
  texte, dit que tout est gratuit et sans inscription, renvoie au lien de la bio, et finit par 5 à 8
  hashtags (#LaRochelle #EmploiLaRochelle #CharenteMaritime, puis selon le sujet).
- `textes_alternatifs` dans le JSON : une description courte de chaque image, pour l'accessibilité.
- **Période des fêtes (du 18 au 31 décembre inclus)** : direction artistique de Noël obligatoire.
  Ajoute `"saison": "noel"` à la racine du JSON (logo enneigé, guirlande, flocons, sapin sur la couverture,
  cadeaux sur la dernière image, story décorée) et mets la couverture en classe `sapin` (vert et or).
  Les images intermédiaires restent en `papier`, la dernière en `rouille`. Le ton peut saluer les fêtes
  (« Bonnes fêtes », « nouvelle année »), un emoji 🎄 ou ✨ dans la légende, sans en faire le sujet du post.
  Hors de cette période, n'utilise ni `saison` ni la classe `sapin`.

Génère les images : `python3 outils/generer.py posts/AAAA-MM-JJ/post.json`. Le script produit les images
du carrousel (`01.jpg`…) et une story verticale (`story.jpg`) qui annonce le post.
Si le script dit qu'un texte est trop long, raccourcis-le et recommence.
**Regarde chaque image et la story** (outil Read) : rien ne doit déborder, se chevaucher ni être coupé.

## 4. Publier

1. `git add posts/AAAA-MM-JJ && git commit -m "Post du AAAA-MM-JJ : <sujet>"`, puis `git push origin HEAD:main`.
2. Note le hash du commit (`git rev-parse HEAD`). Les images sont à
   `https://raw.githubusercontent.com/mguillet443/Lr-travail/<hash>/posts/AAAA-MM-JJ/01.jpg` (02.jpg…).
3. Vérifie chaque adresse : `curl -sI <url>` doit répondre 200 avec `content-type: image/jpeg`.
   Sinon, n'essaie pas de publier : explique le problème.
4. Publie avec l'outil Windsor `execute_action` :
   - `connector` : `instagram`, `account` : `17841422912743277`, `action` : `create_carousel_post` ;
   - `params` : `{"caption": <legende>, "items": [{"image_url": <url 01>, "alt_text": <texte 01>}, …]}`.
   Une seule tentative de publication. En cas d'erreur, ne réessaie pas : explique-la.
5. **Seulement si le carrousel est publié**, publie la story : `execute_action` avec `action` :
   `create_story` et `params` : `{"image_url": <url de story.jpg>}` (même vérification d'adresse avant).
   Une seule tentative ; si elle échoue, le carrousel reste en ligne : signale-le simplement.
   L'API ne permet pas d'ajouter une musique à une story : n'essaie pas, et ne le promets pas.
6. Ajoute une entrée à `historique.json` :
   `{"date": "AAAA-MM-JJ", "sujet": "...", "dossier": "posts/AAAA-MM-JJ", "media_id": "<id du carrousel>", "story_id": "<id de la story ou null>", "images": N}`,
   puis commit (« Historique : post du AAAA-MM-JJ publié ») et push sur `main`.

## 5. Compte rendu

Termine par : le sujet choisi, le nombre d'images, la légende publiée, les identifiants du post et de la
story, et tout problème rencontré.
