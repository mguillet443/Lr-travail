# Posts Instagram de La Rochelle Travail

Carrousels publiés automatiquement deux fois par semaine (mardi et vendredi) sur
[@larochelletravail](https://www.instagram.com/larochelletravail/) par une routine Claude.

- `CONSIGNES.md` : ce que fait la routine, et ses garde-fous. C'est le fichier à modifier pour changer le ton,
  les sujets ou le rythme.
- `outils/generer.py` : dessine les images (JPEG 1080 × 1350) à partir d'un `post.json`.
- `posts/AAAA-MM-JJ/` : chaque post publié (description, images, légende).
- `historique.json` : les posts publiés, pour éviter les doublons et varier les sujets.
- `polices/`, `images/` : polices (Fraunces et Figtree, licence SIL OFL) et logo du site.

Les données viennent de https://la-rochelle-travail.fr/api/instagram.json (informations publiques du site,
sans les offres France Travail).
