"""
Management command : seed_fils_du_destin
Peuple la base de donnees avec "Les Fils du Destin" - scenario complet 3 actes.

Usage : python manage.py seed_fils_du_destin [--reset]
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.stories.models import Story, Scene, Choice

SLUG = 'les-fils-du-destin'

# ---------------------------------------------------------------------------
# SCENES
# Each entry: (narrative, music_file, music_transition, is_starting, is_ending, ending_type)
# ---------------------------------------------------------------------------
SCENES_DATA = {

    # ── PROLOGUE ────────────────────────────────────────────────────────────
    'prologue_matin': (
        "Le soleil de Sparte rechauffe les pierres du village. C'est un matin "
        "comme les autres... ou presque.\n\n"
        "Les trois freres sont ensemble. Kratos taille une branche en epee de "
        "bois. Dimos ramasse du bois a la lisiere. Optimus repare la cloture "
        "a coups de marteau. La mere chante a l'interieur.\n\n"
        "Soudain, un corbeau noir se pose sur le toit et croasse trois fois. "
        "Optimus leve les yeux, mal a l'aise. Une vieille femme qui passe dans "
        "la rue s'arrete, fixe Dimos, et murmure quelque chose "
        "d'incomprehensible avant de disparaitre.\n\n"
        "Qui veux-tu incarner ?",
        'calm_ambient.mp3', 'fade', True, False, None
    ),

    # ── ACTE 1 — VOIE KRATOS ────────────────────────────────────────────────
    'k1_jardin': (
        "Kratos joue dans le jardin quand les cris dechirent l'air. Il court. "
        "Ce qu'il voit le paralyse : un colosse en armure noire gravee de runes "
        "inconnues tient Dimos par le col. Optimus charge en hurlant. Le colosse "
        "ne se retourne meme pas - il attrape le marteau en plein vol et d'un "
        "revers lent et indifferent, frappe Optimus a la tempe. Le bruit est "
        "sourd. Terrible. Optimus s'effondre comme une muraille qui cede.\n\n"
        "Le ravisseur croise le regard de Kratos. Une seconde. Ses yeux sont "
        "vides, comme deux puits sans fond. Puis il s'enfonce dans la Foret "
        "Sombre avec Dimos sur l'epaule.\n\n"
        "Kratos ne peut pas bouger. Ses jambes refusent d'obeir.",
        'horror_intense.mp3', 'instant', False, False, None
    ),
    'k1_optimus_blesse': (
        "Kratos s'agenouille aupres d'Optimus. Son frere aine ouvre un oeil, "
        "attrape le poignet de Kratos avec une force etonnante. Il murmure : "
        "'La marque... sur son cou... Dimos a une marque. C'est pour ca qu'ils "
        "sont venus. Va... sauve-le.' Sa main retombe. Il respire encore, mais "
        "ne se relevera pas seul.\n\n"
        "La mere arrive en courant, s'effondre en larmes sur Optimus. Elle saisit "
        "Kratos par les epaules : 'Ne meurs pas. Ramene ton frere. Et reviens.'\n\n"
        "Kratos retire le bracelet de cuir d'Optimus et le glisse a son poignet. "
        "Un rappel. Une promesse.",
        'calm_ambient.mp3', 'fade', False, False, None
    ),
    'k1_maison_secrets': (
        "En cherchant des vivres, Kratos ouvre un coffre sous le lit de sa mere "
        "qu'il n'avait jamais vu. A l'interieur : une carte partielle de la Foret "
        "Sombre, un flacon d'huile de combat, et une lettre pliee adressee a "
        "'Mon fils aux yeux de cendres'.\n\n"
        "Il reconnait l'ecriture de sa mere mais n'a pas le temps de lire "
        "entierement - il voit les mots 'ton pere', 'Sparte n'est pas ton "
        "origine', et 'si jamais ils reviennent pour lui...' avant de replier "
        "la lettre en hate.\n\n"
        "Il prend la carte. Et maintenant - quelle arme emporter ?",
        'calm_ambient.mp3', 'continuous', False, False, None
    ),
    'k1_foret': (
        "Kratos suit les traces de pas qui s'enfoncent entre les grands arbres "
        "noirs. La foret change rapidement : les oiseaux se taisent, la lumiere "
        "filtre a peine, et une odeur de soufre impregne l'air. Les traces sont "
        "claires - le ravisseur ne cherchait meme pas a se cacher. Il ne "
        "craignait personne.\n\n"
        "Apres une heure de marche, Kratos tombe sur une scene etrange : un "
        "homme enchaine a un arbre, blesse, en armure de marchand. Il halète : "
        "'Attendez... vous n'etes pas l'un d'eux. Je suis Theron, marchand de "
        "Corinthe. Ces soldats transportent un enfant vers le Donjon de Fer, "
        "au nord. J'ai essaye d'intervenir. Erreur.'\n\n"
        "Ses yeux sont trop calmes pour un homme innocent.",
        'tension_rising.mp3', 'instant', False, False, None
    ),
    'k1_theron_fouille': (
        "Dans la bourse de Theron : une piece d'or frappee d'un symbole inconnu "
        "- le meme symbole que sur l'armure du ravisseur.\n\n"
        "Theron palit. 'Je peux tout expliquer...'\n\n"
        "Il ment, ou du moins il cache quelque chose. La question est : "
        "combien vaut sa verite ?",
        'tension_rising.mp3', 'continuous', False, False, None
    ),
    'k1_theron_interroge': (
        "Theron craque. Il etait paye pour surveiller la famille depuis des "
        "semaines et rapporter si Dimos montrait 'des signes de la marque "
        "active'. Il ne pensait pas que l'enlevement aurait lieu si tot.\n\n"
        "Il regrette. Ou il dit regretter.\n\n"
        "Il offre de guider Kratos jusqu'a l'entree du Donjon de Fer en echange "
        "de sa liberte. Un raccourci de deux heures. Un risque de trahison.",
        'tension_rising.mp3', 'continuous', False, False, None
    ),
    'k1_campement': (
        "Kratos decouvre un campement de trois soldats en armure noire autour "
        "d'un feu. Ils rient, boivent. Pas de Dimos ici - mais l'un d'eux porte "
        "la sacoche du marchand Theron. Ce sont clairement des eclaireurs "
        "laisses en arriere-garde.\n\n"
        "Le camp est mal surveille. Ils ne s'attendent pas a etre suivis.",
        'tension_rising.mp3', 'continuous', False, False, None
    ),
    'k1_campement_combat': (
        "Le combat dans l'obscurite est brutal et court. Kratos neutralise deux "
        "soldats mais le troisieme saisit une corne de guerre - Kratos l'atteint "
        "juste a temps.\n\n"
        "Dans le campement fouille : une cle de geolier rouilee et une carte "
        "partielle du Donjon de Fer. Deux informations qui pourraient tout "
        "changer.\n\n"
        "Le Donjon est au nord. Moins d'une heure de marche.",
        'tension_rising.mp3', 'continuous', False, False, None
    ),
    'k1_donjon_porte': (
        "Le Donjon de Fer est une forteresse taillee dans la roche noire, "
        "encastree dans une falaise. Deux gardes imposants flanquent l'entree "
        "principale. Des torches. Des chaines sur les murs. Quelque part "
        "a l'interieur, Dimos attend.\n\n"
        "Kratos s'arrete dans l'ombre des arbres et observe. Plusieurs approches "
        "sont possibles. Chacune a un prix different.",
        'tension_rising.mp3', 'continuous', False, False, None
    ),
    'k1_entree_egouts': (
        "Kratos longe la falaise dans l'obscurite. Apres vingt minutes, il "
        "trouve une bouche d'egout entrouverte. A l'interieur : obscurite totale, "
        "eau froide jusqu'aux genoux, et des bruits de rats.\n\n"
        "Mais aussi... une voix. Une voix de femme qui chante doucement.\n\n"
        "Kratos avance. Derriere une grille rouilee, une jeune femme en robe "
        "de pretresse le fixe avec des yeux immenses. Elle n'a pas crie. "
        "Elle l'attendait, dirait-on.\n\n"
        "'Je suis Lysara, pretresse d'Athena. Capturee il y a trois jours. "
        "Je connais le plan interieur de ce donjon mieux que ses gardes.'",
        'tension_rising.mp3', 'continuous', False, False, None
    ),
    'k1_lysara': (
        "Lysara est libre. Elle etiree ses poignets marques par les cordes, "
        "puis elle montre a Kratos un plan gribouille dans la poussiere.\n\n"
        "'Les prisonniers speciaux sont en dessous. Niveau trois. Il y a une "
        "salle avec cinq portes - le gardien vous posera des questions avant "
        "de vous laisser passer. Repondez avec sagesse, pas avec force.'\n\n"
        "Elle le regarde. 'Je peux vous guider jusqu'a lui.'",
        'tension_rising.mp3', 'continuous', False, False, None
    ),
    'k1_fin_act1': (
        "Kratos entre dans le Donjon de Fer.\n\n"
        "L'air est lourd de poussiere de pierre et d'encens noir. Des torches "
        "projettent des ombres qui dansent sur des murs couverts de symboles "
        "anciens. Quelque part sous ses pieds, son frere attend.\n\n"
        "Ce n'est plus une question de vitesse. C'est une question d'intelligence.\n\n"
        "Kratos serre son arme et descend.",
        'tension_rising.mp3', 'instant', False, False, None
    ),

    # ── ACTE 1 — VOIE DIMOS ─────────────────────────────────────────────────
    'd1_lisiere': (
        "Dimos empile du bois quand il sent une presence derriere lui. Une "
        "odeur - metal, sueur, et quelque chose d'autre. De l'encens noir.\n\n"
        "Avant qu'il puisse se retourner, une main immense lui ecrase la "
        "bouche. Il se debat, crie dans la paume. Il voit Optimus arriver en "
        "courant, marteau leve, les yeux fous d'amour et de rage. Il voit le "
        "revers de main indifferent. Il entend le bruit. Il voit son frere "
        "tomber.\n\n"
        "Puis le monde tourne, et tout devient noir.",
        'horror_intense.mp3', 'instant', False, False, None
    ),
    'd1_chariot': (
        "Dimos se reveille sur de la paille humide. Ses poignets saignent la "
        "ou les cordes mordent la peau. Le chariot cahote sur un chemin de "
        "pierre. Il fait chaud. Deux gardes a l'avant discutent en croyant "
        "leur prisonnier inconscient.\n\n"
        "Dimos garde les yeux mi-clos. Il respire lentement. Il pense.",
        'tension_rising.mp3', 'instant', False, False, None
    ),
    'd1_ecouter': (
        "Dimos fait le mort et ecoute.\n\n"
        "'...la marque s'est activee hier soir selon le devin. Il ne reste "
        "plus beaucoup de temps.'\n"
        "'Et si le rituel echoue ?'\n"
        "'Alors les Oublies se reveillent, et ce n'est plus notre probleme - "
        "ni celui de personne.'\n\n"
        "Un silence. Puis : 'Tu as vu le frere aine ? Il etait courageux.'\n"
        "'Courageux et mort. C'est la meme chose.'\n\n"
        "Dimos serre les mains dans son dos. Optimus. Il ferme les yeux une "
        "fraction de seconde, puis les rouvre. Concentre.",
        'tension_rising.mp3', 'continuous', False, False, None
    ),
    'd1_couteau': (
        "Les doigts de Dimos explorent la paille en silence. Quelque chose "
        "de dur et froid. Un couteau de cuisine casse, peut-etre tombe d'un "
        "chargement precedent. La lame est courte mais assez tranchante.\n\n"
        "Il le glisse dans sa manche sans faire de bruit. Les gardes ne "
        "se sont pas retournes.\n\n"
        "Maintenant - l'utiliser tout de suite, ou attendre le bon moment ?",
        'tension_rising.mp3', 'continuous', False, False, None
    ),
    'd1_fuite_gue': (
        "Le chariot ralentit pour franchir un gue. L'eau clapote contre les "
        "roues. C'est maintenant ou jamais.\n\n"
        "Dimos se glisse vers le bord, calcule la trajectoire. Les roseaux "
        "de la rive sont a trois metres. Si il saute trop tot il atterrit "
        "dans l'eau trop profonde. Trop tard et les gardes le voient.",
        'tension_rising.mp3', 'continuous', False, False, None
    ),
    'd1_interrogatoire': (
        "Le garde retourne Dimos sur le dos et le fixe. Il n'est pas cruel - "
        "il est professionnel. 'Tu es intelligent. Bien. Ecoute-moi. Personne "
        "ne te fera de mal si tu ne te debats pas. Tu es precieux. Trop precieux "
        "pour etre abime.'\n\n"
        "Il reserre les liens et remet Dimos dans le chariot. Mais maintenant, "
        "Dimos sait qu'il est considere comme 'trop precieux pour mourir'. "
        "C'est une information capitale.\n\n"
        "Le garde se rasseoit. Il a l'air presque gene d'avoir parle.",
        'tension_rising.mp3', 'continuous', False, False, None
    ),
    'd1_foret_libre': (
        "Dimos roule dans la boue froide de la rive. Les gardes continuent "
        "sans s'arreter. Il est libre, trempe, seul dans une foret inconnue.\n\n"
        "Ses vetements sont dechires, ses poignets saignent encore. Il ne sait "
        "pas ou il est. Il ne sait pas si Optimus est vivant. Il ne sait pas "
        "si Kratos le cherche.\n\n"
        "Il marche. Apres un moment, il apercoit une lumiere entre les arbres.",
        'calm_ambient.mp3', 'fade', False, False, None
    ),
    'd1_berger': (
        "Un vieux berger et ses chevres. Il s'appelle Argo. Il ne pose aucune "
        "question sur l'etat de Dimos - il a l'air d'avoir tout vu dans sa vie.\n\n"
        "Il lui donne du pain, du lait chaud, et une vieille couverture de "
        "laine. Apres que Dimos mange, Argo dit simplement : 'Le Donjon de "
        "Fer est a deux jours vers le nord. Si c'est la que tu vas.'\n\n"
        "Il ne demande pas comment il le sait.",
        'calm_ambient.mp3', 'continuous', False, False, None
    ),
    'd1_choix_coeur': (
        "Deux jours de marche, de fuite et d'ingenuosite. Dimos arrive aux "
        "abords du Donjon de Fer par ses propres moyens.\n\n"
        "Il apercoit quelqu'un qui approche par l'autre cote de la foret - "
        "une silhouette qu'il reconnaitrait entre mille.\n\n"
        "Kratos.\n\n"
        "Leurs yeux se croisent. Un moment suspendu.\n\n"
        "Puis une alarme resonne dans le Donjon. Des gardes sortent en "
        "courant. Kael, le ravisseur, apparait sur les remparts. Il voit les "
        "deux freres. Il sourit.",
        'horror_intense.mp3', 'instant', False, False, None
    ),
    'd1_fin_sacrifice': (
        "Dimos se retourne vers Kratos et crie : 'Entre par derriere ! Moi "
        "je les emmene avec moi !'\n\n"
        "Avant que Kratos puisse reagir, Dimos marche vers les gardes, les "
        "mains levees. 'Je me rends.'\n\n"
        "Les gardes se precipitent sur lui. Kael descend des remparts, lentement, "
        "les yeux fixes sur l'enfant avec une expression impossible a lire.\n\n"
        "Kratos est seul dans l'ombre des arbres. Une fenetre vient de "
        "s'ouvrir.\n\n"
        "Dimos a choisi.",
        'tension_rising.mp3', 'instant', False, False, None
    ),
    'd1_fin_fuite_info': (
        "Dimos court vers Kratos en criant : 'La marque - c'est elle qu'ils "
        "veulent ! Rituel dans cinq jours ! Il y a une autre fin a la "
        "prophetie - le choix consenti !'\n\n"
        "Les gardes se lancent a leur poursuite. Les deux freres courent dans "
        "la foret, epaule contre epaule, comme ils l'ont toujours fait.\n\n"
        "Ils s'arretent hors de portee, hors d'haleine. Dimos regarde son "
        "frere. 'Je savais que tu viendrais.'\n"
        "'Je savais que tu serais encore debout.'\n\n"
        "Un silence. Puis Dimos : 'Il faut rentrer dans ce donjon.'",
        'tension_rising.mp3', 'fade', False, False, None
    ),

    # ── ACTE 1 — VOIE OPTIMUS ───────────────────────────────────────────────
    'o1_avant_orage': (
        "Optimus coupe du bois. Il frappe en cadence, regulier, confiant. Il "
        "pense a ce soir - sa mere a promis du ragout d'agneau. Kratos lui a "
        "defie une course ce matin. Dimos l'a appele 'le plus fort du village' "
        "et Optimus a ri, fier malgre lui.\n\n"
        "C'est un matin parfait. Ces matins-la le rendent mefiant.\n\n"
        "Il s'arrete. Un corbeau noir sur le toit. L'odeur d'encens sur le vent. "
        "Il serre son marteau sans savoir pourquoi.\n\n"
        "Puis il entend le cri de Dimos.",
        'calm_ambient.mp3', 'fade', False, False, None
    ),
    'o1_charge': (
        "Optimus ne reflechit pas. C'est la son plus grand defaut et sa plus "
        "grande qualite. Il serre son marteau a deux mains, pousse un rugissement "
        "de bete blessee, et charge.\n\n"
        "Le colosse en armure noire se retourne lentement. Tres lentement. "
        "Comme si un enfant qui charge avec un jouet en bois ne meritait pas "
        "plus d'attention.\n\n"
        "Optimus a une fraction de seconde pour choisir son attaque.",
        'horror_intense.mp3', 'instant', False, False, None
    ),
    'o1_chute': (
        "La vision d'Optimus explose en blanc. Ses genoux se derobent. Il "
        "tombe sur la terre poussiereuse du jardin.\n\n"
        "Le ciel de Sparte tourne au-dessus de lui - si bleu, si injustement "
        "bleu.\n\n"
        "Il entend les pas lourds du ravisseur qui repart. Il entend Dimos "
        "crier son nom. Il entend sa mere.\n\n"
        "Et il entend Kratos. Kratos qui arrive trop tard. Dont il voit le "
        "visage changer en une fraction de seconde - l'insouciance effacee "
        "a jamais.\n\n"
        "Optimus tend la main. Kratos la saisit.\n"
        "'Sauve-le...'\n\n"
        "Ce sont les deux seuls mots qui comptent.",
        'horror_intense.mp3', 'continuous', False, False, None
    ),
    'o1_entredeux': (
        "Noir total. Puis une lumiere grise, froide. Des champs vides a perte "
        "de vue. Optimus est debout - sans douleur. Il comprend.\n\n"
        "Une silhouette s'approche. Un vieillard avec un oeil bande et un "
        "baton de marche. Il s'assoit sur une roche inexistante.\n"
        "'Tu as bien fait,' dit le vieillard. 'Pas assez bien pour gagner. "
        "Mais assez bien pour que ca compte.'\n\n"
        "Optimus : 'Mes freres-'\n"
        "'Vivants. Pour l'instant. Tu peux rester ici. Ou tu peux choisir "
        "de leur envoyer quelque chose. Un signe. Ce que les vivants "
        "appellent... du courage au bon moment.'\n\n"
        "Que choisit Optimus ?",
        'calm_ambient.mp3', 'fade', False, False, None
    ),
    'o1_fin_force': (
        "Optimus ferme les yeux dans la lumiere grise.\n\n"
        "Quelque part dans la Foret Sombre, Kratos s'arrete une seconde. "
        "Ses epaules se redressent. Quelque chose de chaud remonte le long "
        "de sa colonne vertebrale - pas de la chaleur physique. Quelque chose "
        "de plus ancien. La certitude absolue, pendant un seul instant, "
        "qu'il n'est pas seul.\n\n"
        "'Votre courage fut immense. Votre force, insuffisante contre ce qui "
        "depasse les hommes. Mais Kratos a senti votre presence au moment "
        "ou il en avait le plus besoin.\n\n"
        "Reposez, Optimus. Votre role dans cette histoire n'est pas termine.'",
        'calm_ambient.mp3', 'fade', False, True, 'neutral'
    ),
    'o1_fin_sagesse': (
        "Optimus ferme les yeux dans la lumiere grise.\n\n"
        "Quelque part dans un chariot qui cahote, Dimos s'arrete de trembler. "
        "Une pensee lui vient - claire, precise, inattendue. Pas la sienne. "
        "Ou plutot : la sienne, mais portee par quelqu'un d'autre.\n"
        "'Sois plus intelligent qu'eux. Pas plus fort.'\n\n"
        "'Votre sagesse fut immense. Vous n'avez pas gagne le combat. "
        "Mais Dimos a su quoi dire au moment crucial - parce que vous "
        "lui avez envoye les mots.\n\n"
        "Reposez, Optimus. Votre role dans cette histoire n'est pas termine.'",
        'calm_ambient.mp3', 'fade', False, True, 'neutral'
    ),
    'o1_fin_repos': (
        "Optimus regarde le vieillard une derniere fois.\n"
        "'Ils n'ont besoin que d'eux-memes.'\n"
        "'Peut-etre,' dit le vieillard. 'Ou peut-etre que la confiance "
        "est elle aussi une force.'\n\n"
        "Optimus sourit malgre lui. Il s'assoit sur l'herbe froide de ce "
        "monde-entre-deux. Il pense au ragout d'agneau qu'il ne mangera "
        "jamais. A la course qu'il n'a pas couru.\n\n"
        "'Votre sacrifice fut reel. Vos freres portent votre souvenir "
        "comme une armure invisible.\n\n"
        "L'histoire continue. Elle a besoin d'eux maintenant.'",
        'calm_ambient.mp3', 'fade', False, True, 'neutral'
    ),

    # ── ACTE 2 — VOIE KRATOS ────────────────────────────────────────────────
    'k2_entree_donjon': (
        "Kratos entre dans le Donjon de Fer. Sur le premier mur qu'il longe : "
        "des fresques gravees dans la pierre noire. Des scenes de guerre. Des "
        "dieux qu'il ne reconnait pas. Au centre, une silhouette d'enfant "
        "entouree de chaines brisees - ou de chaines serrees. Les deux versions "
        "existent cote a cote. Deux fins possibles pour la meme prophetie.\n\n"
        "Kratos s'arrete. Ses doigts touchent la pierre.",
        'tension_rising.mp3', 'instant', False, False, None
    ),
    'k2_fresques_detail': (
        "Lysara traduit les symboles a voix basse, les yeux brillants d'une "
        "terreur melee de fascination.\n\n"
        "'C'est du Pre-Spartiate... tres ancien. Ca dit : L'Enfant Marque est "
        "la cle. S'il meurt avant sa douzieme annee, le verrou tient. S'il "
        "vit... le verrou se brise et les Oublies marchent.'\n\n"
        "Un silence.\n"
        "'Kael ne ment pas,' dit-elle. 'Il croit vraiment sauver le monde "
        "en tuant ton frere.'\n"
        "'Et toi ?' demande Kratos.\n"
        "'Moi... je crois que les propheties sont ecrites par des hommes "
        "qui veulent avoir raison.'",
        'tension_rising.mp3', 'continuous', False, False, None
    ),
    'k2_salle_cinq_portes': (
        "Kratos descend un escalier en colimacon taille dans le roc brut. "
        "L'air devient glacial. Les torches laissent place a des cristaux "
        "luminescents bleu-vert - une lumiere froide, presque vivante.\n\n"
        "Au bas : une salle circulaire avec cinq portes. Sur chaque porte, "
        "un symbole grave : FEU / EAU / VENT / FOUDRE / OMBRE.\n\n"
        "Au centre, un vieillard enchaine au sol - une chaine si longue "
        "qu'elle semble decorative. Il parle sans ouvrir les yeux :\n"
        "'Un vivant. Cela fait longtemps. L'enfant marque est derriere la "
        "porte de l'Ombre. Mais les quatre autres portes te donneront des "
        "raisons de ne jamais repartir d'ici.'\n\n"
        "Il ouvre les yeux. Ils sont entierement blancs.\n"
        "'Trois questions. Je reponds a trois. Apres, tu choisis.'",
        'calm_ambient.mp3', 'fade', False, False, None
    ),
    'k2_gardien_lignee': (
        "Le gardien repond lentement, comme s'il depensait des mots rares.\n\n"
        "'La marque apparait une fois par generation dans une lignee "
        "particuliere. Votre lignee. Ton frere n'a pas ete choisi par hasard. "
        "Vous n'etes pas qui vous croyez etre. Votre pere... n'etait pas "
        "de Sparte.'\n\n"
        "La lettre dans la maison. 'Si jamais ils reviennent pour lui...'\n\n"
        "'Comment vaincre Kael ?' demande Kratos.\n"
        "'Tu ne peux pas. Pas encore. Kael puise sa force dans la meme "
        "source que la marque de ton frere. Ils sont lies. Pour le blesser "
        "vraiment, il faudrait une arme forgee dans la lumiere d'une etoile "
        "morte. Ou... l'amour d'un frere. Les deux sont rares.'\n\n"
        "'Quelle est la deuxieme fin de la prophetie ?'\n"
        "'Si l'Enfant Marque choisit lui-meme de porter ses chaines, le "
        "verrou tient aussi. Nul besoin de mort. Un sacrifice consenti "
        "vaut mille meurtres.'",
        'calm_ambient.mp3', 'continuous', False, False, None
    ),
    'k2_porte_foudre': (
        "Une salle longue et etroite. Au fond, un jeune prisonnier enchaine "
        "au mur - pas beaucoup plus vieux que Kratos. Armure brisee aux "
        "couleurs d'une cite inconnue. Ses poignets sont attaches au-dessus "
        "de sa tete depuis trop longtemps.\n\n"
        "Il leve les yeux. 'Tu n'es pas d'ici.' Pas une question.\n\n"
        "Son nom est Zenos. Soldat d'une cite cotiere, capture il y a trois "
        "semaines lors d'une mission de reconnaissance. Il ne sait rien de "
        "la prophetie. Mais il connait le Donjon comme sa poche - il a eu "
        "le temps de l'etudier a travers les barreaux.\n\n"
        "'Je peux te guider jusqu'aux cellules profondes. Si tu me sors "
        "d'ici.'",
        'tension_rising.mp3', 'continuous', False, False, None
    ),
    'k2_forge_interdite': (
        "La chaleur frappe Kratos comme un mur. La salle est immense - une "
        "forge souterraine encore active, ses braises entretenues par on ne "
        "sait quoi depuis des siecles.\n\n"
        "Sur les murs, des armes dans des supports de pierre. La plupart "
        "sont trop grandes pour un humain. Trop etranges pour un forgeron "
        "ordinaire.\n\n"
        "Une seule arme est a taille humaine : une paire de lames courtes "
        "enchainees ensemble, le metal d'un noir brillant veine de rouge "
        "incandescent. Elles irradient une chaleur douce, presque vivante.\n\n"
        "Kratos tend la main.",
        'horror_intense.mp3', 'instant', False, False, None
    ),
    'k2_lames_inscription': (
        "Grave sur la garde de chaque lame, en tout petit :\n"
        "'A celui qui brule assez pour tout perdre.'\n\n"
        "Kratos regarde ses mains. Il pense a Optimus. Il pense a Dimos "
        "quelque part derriere un mur de pierre.\n\n"
        "Il brule. Suffisamment.",
        'horror_intense.mp3', 'continuous', False, False, None
    ),
    'k2_couloir_cellules': (
        "Le couloir des cellules est long, humide, et silencieux d'une facon "
        "qui fait mal aux oreilles. Des cellules vides de chaque cote - "
        "certaines montrent des traces de presence ancienne. Des noms "
        "griffes dans la pierre. Des marques de jours comptes.\n\n"
        "Puis Kratos entend quelque chose.\n\n"
        "Une voix familiere. Dimos - qui fredonne. Tout bas. Le meme air "
        "que leur mere chantait le soir.\n\n"
        "Kratos s'arrete devant une cellule au fond. Il colle son front "
        "contre les barreaux froids.\n"
        "'Dimos.'\n\n"
        "Un silence.\n"
        "'...Kratos ?'",
        'tension_rising.mp3', 'fade', False, False, None
    ),
    'k2_reunion_freres': (
        "Dimos s'approche des barreaux. Il a un oeil legerement tumefie. "
        "Ses vetements sont dechires. Mais ses yeux sont vifs - alertes. "
        "Il n'a pas pleure. Ou il a fini de pleurer.\n\n"
        "'Optimus ?' demande Dimos.\n\n"
        "Le visage de Kratos repond avant sa bouche.\n\n"
        "Dimos ferme les yeux une seconde. Une seule. Puis il les rouvre. "
        "'Il faut qu'on parte d'ici. J'ai entendu des choses. La "
        "prophetie... il y a une deuxieme fin. Un sacrifice consenti. "
        "Et Kael a un point faible - la marque sur mon cou est aussi "
        "sa source de pouvoir. Ils sont lies.'\n\n"
        "Kratos absorbe cela. 'On parle de ca dehors. Comment on sort ?'",
        'tension_rising.mp3', 'continuous', False, False, None
    ),
    'k2_liberation': (
        "Kratos saisit les barreaux. Ils sont rouilles mais epais. Il "
        "grogne, tire, les muscles des epaules en feu.\n\n"
        "Un barreau cede dans un grincement terrible. Dimos se glisse "
        "dehors.\n\n"
        "Les deux freres se regardent une fraction de seconde - la meme "
        "facon dont on regarde quelqu'un qu'on croyait perdu.\n\n"
        "Puis la cloche resonne dans tout le Donjon.",
        'horror_intense.mp3', 'instant', False, False, None
    ),
    'k2_alarme': (
        "'Kael sait,' dit Dimos. Calme. Trop calme.\n"
        "'Comment ?'\n"
        "'La marque. Il sent quand je bouge trop loin de la salle du rituel. "
        "On est relies.'\n\n"
        "Le couloir se remplit de lumieres de torches qui approchent "
        "des deux cotes. Des pas lourds. Nombreux.\n\n"
        "'Il y a un puits d'aeration dans la salle du rituel,' dit Dimos. "
        "'Une troisieme sortie. Les gardes ne l'utilisent jamais.'\n\n"
        "Decider vite.",
        'horror_intense.mp3', 'continuous', False, False, None
    ),

    # ── ACTE 2 — VOIE DIMOS ─────────────────────────────────────────────────
    'd2_cellule_speciale': (
        "Dimos est dans une cellule differente - plus grande, mieux eclairee. "
        "Comme une chambre, presque. On lui apporte de la nourriture. Un "
        "garde reste poste devant sa porte mais ne le brutalise pas.\n\n"
        "'Tu es precieux,' lui a dit Kael en le regardant traverser la cour "
        "interieure. 'Ne l'oublie pas. Et ne le gaspille pas.'\n\n"
        "Dimos s'assoit sur sa paillasse et observe la cellule "
        "methodiquement. Fenetre trop petite. Barreaux neufs. Mais le "
        "garde change toutes les deux heures. Et il pose son casque sur "
        "le sol a chaque fois.",
        'tension_rising.mp3', 'instant', False, False, None
    ),
    'd2_plan_evasion': (
        "Dimos analyse ses options.\n\n"
        "Option un : simuler une crise de panique. Un enfant en detresse "
        "peut deconcentrer un garde.\n\n"
        "Option deux : attendre la releve et etudier la nouvelle recrue "
        "- peut-etre moins experimente.\n\n"
        "Option trois : le couteau casse. Si Dimos l'a toujours, les "
        "barreaux ont des supports vieux de plusieurs siecles.\n\n"
        "Il reste cinq jours avant le rituel. Peut-etre moins.",
        'tension_rising.mp3', 'continuous', False, False, None
    ),
    'd2_crise_panique': (
        "Dimos tremble, pleure, appelle sa mere. Il met tout ce qu'il "
        "a dans cette performance.\n\n"
        "Le garde resiste deux minutes. Puis trois. Puis il entrouvre la "
        "porte. 'Tais-toi, gamin.'\n\n"
        "Dimos regarde la cle accrochee a sa ceinture. Un seul mouvement.\n\n"
        "Test de dexterite : attraper la cle pendant que le garde le "
        "repousse. Ses doigts effleurent le metal...",
        'tension_rising.mp3', 'continuous', False, False, None
    ),
    'd2_kael_visite': (
        "Kael entre dans la cellule de Dimos seul. Sans armes visibles. "
        "Il s'assoit en face de l'enfant avec une lourdeur qui n'est pas "
        "de la fatigue mais du poids.\n\n"
        "Il observe la marque sur le cou de Dimos longuement.\n"
        "'Est-ce qu'elle fait mal ?'\n"
        "'Non.'\n"
        "'Elle devrait. C'est une marque de sacrifice.'\n\n"
        "Une pause. 'Tu sais ce que tu es ?'",
        'calm_ambient.mp3', 'fade', False, False, None
    ),
    'd2_kael_dialogue': (
        "Kael se fige une fraction de seconde.\n\n"
        "Puis quelque chose change dans son expression. Il cesse de voir "
        "un enfant. Il commence a voir quelque chose d'autre.\n"
        "'Qui t'a dit ?'\n"
        "'Les murs parlent ici.'\n\n"
        "Un silence long. Puis Kael, pour la premiere fois, sourit.\n"
        "'Tu es different des autres marques. Les autres avaient peur. "
        "Toi...' Il secoue la tete. 'Ton frere va venir te chercher.'\n"
        "'Je sais.'\n"
        "'Il mourra en essayant.'\n"
        "'Peut-etre.' Dimos soutient son regard. 'Ou peut-etre que vous "
        "vous sous-estimez tous les deux.'\n\n"
        "Kael quitte la cellule sans avoir obtenu ce qu'il cherchait.",
        'calm_ambient.mp3', 'continuous', False, False, None
    ),
    'd2_mira': (
        "La nuit tombe sur le Donjon. Dimos entend quelqu'un gratter "
        "le mur entre deux cellules. Un code en tapotements - trois "
        "coups, pause, deux coups, pause, un coup. Un code enfantin. "
        "Celui des enfants du village pour communiquer en classe.\n\n"
        "Dimos tape en retour.\n\n"
        "Une voix etouffee traverse la pierre : 'Je savais que c'etait "
        "toi. J'ai reconnu ta facon de marcher dans le couloir.'\n\n"
        "Mira. La fille du boulanger. Capturee deux semaines plus tot. "
        "Dimos ne savait meme pas qu'elle avait disparu.\n\n"
        "'Chaque nuit a minuit exactement, tous les gardes du couloir "
        "se reunissent en salle de garde pendant sept minutes. Sept "
        "minutes ou les couloirs sont vides.'",
        'calm_ambient.mp3', 'continuous', False, False, None
    ),
    'd2_marque_eveille': (
        "Minuit approche. Dimos est assis dans le noir quand ca commence "
        "- une chaleur sur son cou, la ou est la marque. Pas douloureuse. "
        "Pulsante. Comme un second coeur.\n\n"
        "Et soudain il sent quelque chose. Une presence dans le Donjon. "
        "Proche. Familiere.\n\n"
        "Kratos est la.\n\n"
        "La marque lui indique sa direction aussi clairement qu'une "
        "boussole. Il a sept minutes.",
        'tension_rising.mp3', 'instant', False, False, None
    ),

    # ── CONVERGENCE ACTE 2 ──────────────────────────────────────────────────
    'c2_retrouvailles': (
        "Kratos et Dimos se trouvent dans le meme couloir.\n\n"
        "Ils se percutent presque au coin d'un couloir, s'arretent net, "
        "et se regardent une fraction de seconde - puis Dimos pousse Kratos "
        "dans l'ombre d'une alcove. Des gardes passent.\n\n"
        "Dans l'obscurite, ils se retrouvent. Dimos a l'oeil tumefie. "
        "Kratos a du sang sur les mains qui n'est pas le sien.\n\n"
        "Devant eux : une grande porte de bois renforcee de metal noir. "
        "Une lumiere froide filtre en dessous.\n\n"
        "La salle du rituel.\n\n"
        "La chaleur de la marque de Dimos devient intense, presque "
        "insupportable.",
        'tension_rising.mp3', 'fade', False, False, None
    ),
    'c2_salle_rituel': (
        "La salle du rituel est circulaire, haute de plafond, taillee dans "
        "le roc vif. Des symboles identiques a la marque de Dimos sont "
        "graves partout - sur les murs, le sol, le plafond. Au centre, une "
        "table de pierre. Des chaines. De l'encens noir qui brule en "
        "spirales lentes.\n\n"
        "Et Kael, debout au centre, dos a la porte, qui ne se retourne pas.\n\n"
        "'Je savais que vous viendriez ensemble. La prophetie ne le "
        "precisait pas. Mais... ca a du sens.'\n\n"
        "Il se retourne. Il ne porte pas son armure. Juste une tunique "
        "sombre. Il parait plus humain ainsi. Plus fatigue.\n\n"
        "'Je n'ai pas le choix,' dit-il. Pas comme une excuse. Comme un fait. "
        "'J'ai vu une ville entiere disparaitre en une nuit quand le verrou "
        "a failli ceder, il y a cinquante ans. J'etais la.'\n"
        "'Cinquante ans ?' dit Kratos.\n"
        "'Je ne suis pas tout a fait humain non plus.'",
        'horror_intense.mp3', 'instant', False, False, None
    ),
    'c2_kael_revele': (
        "Kael ouvre les mains - pas en geste de paix. En geste de fatigue.\n\n"
        "'La prophetie a deux auteurs,' dit-il. 'Le premier voulait la mort. "
        "Le deuxieme a ajoute une ligne que personne ne lit jusqu'au bout : "
        "Ou que l'Enfant Marque brise lui-meme ses chaines devant les "
        "Gardiens du Verrou.'\n"
        "'Et les Gardiens du Verrou, c'est qui ?' demande Kratos.\n\n"
        "Kael les regarde tous les deux.\n\n"
        "'Vous.'\n\n"
        "Un silence total dans la salle.\n\n"
        "'Votre lignee porte la marque ET le pouvoir de la sceller. Les "
        "Dieux Oublies ne peuvent pas se reveiller si les Gardiens sont "
        "en vie et consentants. C'est pour ca qu'ils ont essaye de vous "
        "separer. De vous affaiblir. De vous faire peur.'",
        'horror_intense.mp3', 'continuous', False, False, None
    ),
    'c2_dimos_parle': (
        "Dimos s'avance seul vers le centre de la salle.\n\n"
        "Kratos fait un pas pour le retenir - Dimos leve la main sans "
        "se retourner.\n\n"
        "'J'ai entendu ce qu'il t'a dit, gardien,' dit Dimos a Kael. "
        "'La deuxieme fin. Pas la mort. Le choix.'\n\n"
        "Kael ne dit rien.\n\n"
        "'Si je choisis moi-meme de porter la marque. De la reconnaitre. "
        "De ne pas la fuir. Le verrou tient, c'est ca ?'\n"
        "'...c'est ce que dit le texte.'\n"
        "'Alors montre-moi comment faire.'\n\n"
        "Kratos : 'Dimos-'\n"
        "'Kratos.' Dimos se retourne. Il a les yeux secs. Il a l'air "
        "infiniment plus vieux que son age. 'Optimus a dit sauve-le. Je "
        "ne veux pas etre sauve. Je veux choisir.'",
        'calm_ambient.mp3', 'fade', False, False, None
    ),

    # ── FINS ACTE 2 → ACTE 3 ────────────────────────────────────────────────
    'c2_violence': (
        "Le combat est bref et brutal. Kael est fort - mais pas invincible. "
        "Il recule. Recule encore. Finalement, il tombe a genoux.\n\n"
        "Il leve les yeux vers Kratos. Pas de peur. De resignation.\n"
        "'Tu as gagne le combat. Tu n'as pas resolu le probleme.'\n\n"
        "Derriere eux, les murs commencent a vibrer. Les symboles sur le "
        "sol brillent d'un rouge profond. La marque sur le cou de Dimos "
        "s'embrase - il crie, se tord de douleur.\n"
        "'Le verrou...' halete Kael depuis le sol. '...se brise des que "
        "je meurs.'\n\n"
        "Kratos tient son arme levee. Kael respire difficilement. "
        "Dimos crie son nom.\n\n"
        "Quelle decision prendre ?",
        'horror_intense.mp3', 'continuous', False, False, None
    ),
    'c2_kael_enchaine': (
        "Kratos abaisse son arme. Il attache Kael avec ses propres chaines.\n\n"
        "Les murs cessent de vibrer. La marque de Dimos refroidit. "
        "Kael inconscient, enchaine a sa propre table de rituel.\n\n"
        "Les freres se regardent dans le silence soudain de la salle.\n"
        "'Et maintenant ?' demande Dimos.\n"
        "'Maintenant on rentre. Et on trouve une vraie reponse avant que "
        "quelqu'un le libere.'\n\n"
        "Le probleme de la prophetie reste entier. Kael est vivant. "
        "Ses disciples sont en route.\n\n"
        "La course commence.",
        'tension_rising.mp3', 'fade', False, False, None
    ),
    'c2_kael_tue': (
        "L'arme tombe.\n\n"
        "Pendant une seconde - rien.\n\n"
        "Puis les murs du Donjon de Fer tremblent. Les cristaux dans les "
        "parois eclatent un a un. La marque sur le cou de Dimos brule "
        "comme un fer rouge - il s'effondre en hurlant. Kratos se precipite "
        "sur lui mais ne peut rien faire.\n\n"
        "Le sol s'ouvre en fissures lumineuses. Quelque part tres profond "
        "sous la terre, quelque chose se reveille.\n\n"
        "Kratos tient son frere dans ses bras au milieu d'une salle qui "
        "s'effondre. Il n'a rien resolu. Il a tout brise.\n\n"
        "'Votre force etait reelle. Mais la force seule ne suffit pas "
        "contre des forces aussi anciennes. Certaines victoires ressemblent "
        "a des defaites - et certaines defaites sont des lecons.\n\n"
        "Recommencez. L'histoire a besoin d'une autre reponse.'",
        'horror_intense.mp3', 'continuous', False, True, 'bad'
    ),
    'c2_alliance': (
        "Kael propose un pacte.\n\n"
        "'Je peux vous guider. Les vrais Gardiens du Verrou sont eparpilles "
        "a travers les cites antiques. Votre pere les connaissait. Je les "
        "connais aussi. Ensemble, nous pouvons trouver la solution "
        "permanente avant que mes anciens maitres ne comprennent ce qui "
        "s'est passe ici.'\n\n"
        "La mefiance est totale. La logique est imparable.\n\n"
        "Kratos regarde Dimos. Dimos regarde Kael.\n"
        "'Si tu nous trahis,' dit Dimos calmement, 'je te le ferai regretter "
        "moi-meme.'\n\n"
        "Kael acquiesce. 'C'est juste.'",
        'calm_ambient.mp3', 'fade', False, False, None
    ),
    'c2_sacrifice_consenti': (
        "Le rituel du Consentement prend trois minutes. Dimos repete des "
        "mots anciens en tenant les mains de Kratos de chaque cote.\n\n"
        "La marque sur son cou brille - blanc pur cette fois, pas rouge. "
        "Puis la lumiere s'eteint doucement.\n\n"
        "Dimos touche son cou. La marque est toujours la. Mais elle est "
        "froide. Inerte.\n\n"
        "Kael s'effondre sur un genou - pas de douleur, d'epuisement. "
        "'C'est... fini. Le verrou tient.' Il leve les yeux vers Dimos "
        "avec quelque chose qui ressemble a de la stupefaction. 'En "
        "quatre cents ans... c'est la premiere fois qu'un Marque choisit.'\n\n"
        "La menace immediate est levee. Mais Kael previent - les Dieux "
        "Oublies ne s'endormiront pas eternellement. Il faut comprendre "
        "l'origine de la lignee. Trouver une solution permanente.",
        'calm_ambient.mp3', 'fade', False, False, None
    ),

    # ── ACTE 3 — BRANCHE A : LA COURSE ──────────────────────────────────────
    'a3_retour_sparte': (
        "L'aube trouve les deux freres sur la route du retour. Dimos "
        "boite legerement. Ils ne parlent pas depuis une heure.\n\n"
        "Quand ils arrivent au village, quelque chose a change. Les gens "
        "s'arretent de travailler pour les regarder. Pas avec la joie d'un "
        "retour - avec quelque chose de plus complique. De la peur melee "
        "de respect. Un enfant montre Kratos du doigt et sa mere lui baisse "
        "le bras vivement.\n\n"
        "Sur la porte de leur maison : un symbole grave dans le bois. "
        "Le symbole du verrou, encercle d'une spirale.\n\n"
        "'Les disciples de Kael,' murmure Dimos.\n"
        "'Ou ceux qui veulent finir ce qu'il n'a pas termine.'",
        'calm_ambient.mp3', 'fade', False, False, None
    ),
    'a3_maison_lettre': (
        "Optimus est vivant. Alite, la tete bandee, mais vivant. Il ouvre "
        "les yeux quand les deux freres entrent dans la chambre.\n\n"
        "Leur mere entre. Son visage est celui de quelqu'un qui portait "
        "un secret depuis des annees et vient de poser le poids a terre. "
        "Elle tient la lettre.\n"
        "'Votre pere,' dit-elle. 'N'etait pas de Sparte.'\n\n"
        "La lettre entiere, maintenant. Leur pere s'appelait Deimos - "
        "comme le fils qu'il aurait un jour, qu'il pressentait. Il etait "
        "le dernier Gardien du Verrou vivant. Avant de mourir, il a cache "
        "ses notes dans trois endroits differents a travers la Grece.\n\n"
        "Ces notes revelent ou trouver les autres Gardiens. Et comment "
        "sceller le verrou de facon permanente.",
        'calm_ambient.mp3', 'continuous', False, False, None
    ),
    'a3_revelation_pere': (
        "La carte dans les notes du pere. Trois symboles. Trois cites.\n\n"
        "Corinthe - 'la pretre qui connait les noms anciens'.\n"
        "Argos - 'le forgeron qui garde la cle de lumiere'.\n"
        "La Cite Oubliee - 'la ou les fils du destin se reunissent'.\n\n"
        "Kael, enchaine dans le Donjon de Fer, sera libere par ses "
        "disciples d'ici quelques jours. Quand ca arrivera, il reprendra "
        "la traque. Les freres ont une avance. C'est tout.\n\n"
        "Optimus etire un bras depuis son lit. 'Allez. Je serai debout "
        "quand vous reviendrez.' Sa voix est rauque mais ferme.",
        'calm_ambient.mp3', 'continuous', False, False, None
    ),
    'a3_chemin_corinthe': (
        "Trois jours de route. Kratos et Dimos voyagent vite et leger, "
        "dormant quand ils ne peuvent plus avancer.\n\n"
        "A Corinthe, ils trouvent la pretresse - une femme agee aux yeux "
        "clairs qui ne semble pas surprise de les voir. Elle regarde la "
        "marque de Dimos et dit simplement : 'Je vous attendais. Votre "
        "pere m'avait dit que vous viendriez un jour.'\n\n"
        "Elle leur donne le premier fragment du Sceau - une pierre grave "
        "aux symboles anciens. 'Il en faut trois. Le forgeron d'Argos "
        "garde le second. Le troisieme est a la Cite Oubliee.'\n\n"
        "Elle hesite. 'Mais sachez - le chemin vers la Cite Oubliee "
        "traverse les terres des Gardiens Corrompus. Des hommes qui ont "
        "choisi le cote des Oublies.'",
        'tension_rising.mp3', 'fade', False, False, None
    ),
    'a3_forgeron_argos': (
        "Le forgeron d'Argos est un homme aux mains brulees par des "
        "decennies de forge. Il examine la marque de Dimos avec des pinces "
        "- pas par cruaute, par habitude professionnelle.\n\n"
        "'Votre pere a forge ca,' dit-il en montrant un pendentif de metal "
        "sombre. 'Le second fragment. Il savait qu'il ne vivrait pas assez "
        "longtemps pour tout finir lui-meme.'\n\n"
        "Mais il y a un probleme. Un groupe d'hommes en tunique grise "
        "est arrive en ville ce matin. Ils cherchent deux jeunes garcons "
        "voyageant seuls. L'un porte une marque sur le cou.\n\n"
        "Les freres sont reperes. La Cite Oubliee maintenant - ou "
        "affronter les disciples ici.",
        'tension_rising.mp3', 'continuous', False, False, None
    ),
    'a3_cite_oubliee': (
        "La Cite Oubliee n'est pas une cite. C'est ce qu'il en reste.\n\n"
        "Des colonnes effondrees. Des murs a moitie debout recouverts de "
        "la meme ecriture Pre-Spartiate que dans le Donjon de Fer. Et au "
        "centre, intact, un autel circulaire avec trois encoches - la taille "
        "exacte des trois fragments.\n\n"
        "Les freres arrivent au coucher du soleil.\n\n"
        "Ils ne sont pas seuls. Trois hommes en tunique grise les "
        "attendaient. Et derriere eux - Kael, libere plus tot que prevu. "
        "Son visage ne trahit aucune emotion.\n"
        "'Vous avez les fragments,' dit-il. 'Je vous en felicite.'\n\n"
        "Il fait un pas en avant. 'Maintenant - posez-les sur l'autel, "
        "ou tout ce que vous avez fait ne servira a rien.'",
        'horror_intense.mp3', 'instant', False, False, None
    ),
    'a3_confrontation_finale': (
        "Kael se bat pour les fragments - ou aide les freres a les poser.\n\n"
        "L'issue depend de tout ce qui est venu avant : les alliés trouves, "
        "les informations recoltes, les choix moraux faits en chemin.\n\n"
        "Dimos s'approche de l'autel. Ses mains ne tremblent pas. Il "
        "place le premier fragment, puis le second.\n\n"
        "Le troisieme est dans la Cite Oubliee elle-meme - grave dans "
        "la pierre de l'autel depuis le debut. Il suffit de poser les "
        "deux autres pour que les trois se reconnectent.\n\n"
        "La marque sur le cou de Dimos s'embrase une derniere fois.\n\n"
        "Blanche. Froide. Puis - rien.",
        'horror_intense.mp3', 'continuous', False, False, None
    ),
    'a3_fin_bonne': (
        "Le silence qui suit est absolu.\n\n"
        "Les trois disciples en tunique grise s'arretent net, les yeux "
        "vides, comme des marionnettes dont on vient de couper les fils. "
        "Ils s'effondrent doucement sur la pierre ancienne.\n\n"
        "Kael reste debout. Il regarde ses mains - et pour la premiere "
        "fois depuis cinquante ans, elles ne tremblent pas.\n"
        "'C'est... fini,' dit-il. Sa voix est celle d'un homme tres vieux "
        "qui vient d'oublier une douleur si ancienne qu'il ne savait plus "
        "qu'il la portait.\n\n"
        "Kratos et Dimos sont debout sur les ruines de la Cite Oubliee, "
        "sous un ciel de nuit plein d'etoiles.\n\n"
        "'On rentre,' dit Dimos.\n"
        "'On rentre,' repond Kratos.\n\n"
        "Quelque part en chemin, une partie de la marque de leur pere "
        "s'eteint pour toujours. Et quelque chose de nouveau commence.",
        'calm_ambient.mp3', 'fade', False, True, 'good'
    ),
    'a3_fin_neutre': (
        "Le verrou est scelle. Pour l'instant.\n\n"
        "Mais Kael s'est echappe dans la confusion finale. Et les disciples "
        "des Dieux Oublies sont nombreux - bien plus nombreux que les "
        "trois qui gardaient la Cite Oubliee ce soir.\n\n"
        "Dimos regarde sa main. La marque est froide. Inerte. Pour combien "
        "de temps ?\n\n"
        "'Nous avons gagne ce soir,' dit Kratos. 'Ca suffit pour ce soir.'\n\n"
        "La route vers Sparte est longue. Optimus les attend. Leur mere "
        "les attend. Tout le reste peut attendre jusqu'a demain.\n\n"
        "Parfois la victoire ressemble exactement a ca - survivre, "
        "rentrer, et recommencer demain.",
        'calm_ambient.mp3', 'fade', False, True, 'neutral'
    ),
    'a3_fin_mauvaise': (
        "Les fragments sont poses.\n\n"
        "Mais trop tard. Ou pas exactement comme il le fallait.\n\n"
        "L'autel brille - puis s'eteint. La marque de Dimos brule "
        "d'un rouge profond. Quelque chose en dessous de la Cite "
        "Oubliee bouge. Respire.\n\n"
        "Les freres courent. Ils courent longtemps.\n\n"
        "Ce soir-la, dans un village lointain, des gens regardent "
        "l'horizon et voient quelque chose qu'ils ne savent pas nommer. "
        "Quelque chose de tres ancien. Qui se souvient d'avoir ete libre.\n\n"
        "La course n'est pas terminee. Elle vient juste de commencer "
        "vraiment. Recommencez - avec ce que vous savez maintenant.",
        'horror_intense.mp3', 'continuous', False, True, 'bad'
    ),

    # ── ACTE 3 — BRANCHE B : LA QUETE ───────────────────────────────────────
    'b3_pacte': (
        "Kael les guide hors du Donjon de Fer par un chemin qu'aucun "
        "garde ne surveille - il a construit ce Donjon, ou du moins il "
        "le connait mieux que ceux qui l'habitent.\n\n"
        "A l'air libre, il s'arrete et se retourne vers les deux freres.\n"
        "'Votre pere m'a parle de vous. Avant de mourir. Il m'a dit "
        "que si jamais la marque s'activait, ses fils trouveraient un "
        "moyen que lui n'avait pas trouve.'\n\n"
        "Un silence. 'Il avait confiance en vous.'\n"
        "'Il ne nous connaissait pas,' dit Kratos.\n"
        "'Non,' repond Kael. 'Mais il vous aimait quand meme.'\n\n"
        "Ils marchent. La route est longue. La mefiance est epaisse "
        "comme du brouillard. Mais ils marchent.",
        'calm_ambient.mp3', 'fade', False, False, None
    ),
    'b3_voyage': (
        "Quinze jours de route. Kael guide. Kratos surveille Kael. "
        "Dimos observe les deux.\n\n"
        "En chemin, des choses se revelent peu a peu. Kael a perdu "
        "sa famille quand une ville a ete detruite par les Oublies - "
        "c'est pour ca qu'il sert les Dieux Oublies depuis. Pas par "
        "conviction. Par peur que ca recommence.\n\n"
        "Dimos lui demande un soir : 'Si on reussit - si le verrou "
        "tient vraiment - qu'est-ce que tu feras ?'\n\n"
        "Kael regarde le feu longtemps avant de repondre. 'Je "
        "ne sais pas. Je ne me suis jamais pose la question.'",
        'calm_ambient.mp3', 'continuous', False, False, None
    ),
    'b3_trahison': (
        "Trois jours avant la Cite Oubliee, Kratos trouve quelque chose "
        "dans les affaires de Kael pendant qu'il dort.\n\n"
        "Un message grave sur une tablette de cire. En symboles des "
        "Dieux Oublies. Kratos ne peut pas tout lire - mais il reconnait "
        "les symboles pour 'enfant', 'marque', et 'livrer'.\n\n"
        "Kael a peut-etre prevu de les trahir a la Cite Oubliee.\n\n"
        "Ou peut-etre que le message est vieux. De l'epoque d'avant.\n\n"
        "Dimos dormait. Kratos tient la tablette. Il peut reveiller "
        "son frere. Il peut confronter Kael. Ou il peut attendre et "
        "surveiller - avoir la certitude avant d'agir.",
        'tension_rising.mp3', 'instant', False, False, None
    ),
    'b3_cite_oubliee': (
        "La Cite Oubliee. Les memes ruines. Le meme autel circulaire.\n\n"
        "Kael s'arrete devant l'autel et pose quelque chose sur la pierre "
        "- le troisieme fragment du Sceau. Il l'avait depuis le debut.\n\n"
        "'Votre pere me l'avait confie,' dit-il sans se retourner. 'En "
        "me disant que je saurais quand le moment serait venu de "
        "le donner.'\n\n"
        "Il se retourne. Ses yeux sont fatigues. Humains.\n"
        "'Le moment est venu. Finissez ce que votre pere a commence.'",
        'horror_intense.mp3', 'instant', False, False, None
    ),
    'b3_fin_bonne': (
        "Les trois fragments sont reunis.\n\n"
        "Dimos les pose sur l'autel - et cette fois Kael est la, "
        "debout a cote d'eux, pas en face d'eux.\n\n"
        "La lumiere qui monte de l'autel est blanche, froide, et "
        "absolument silencieuse. La marque sur le cou de Dimos "
        "pulse une derniere fois - et s'eteint.\n\n"
        "Pour de vrai, cette fois.\n\n"
        "Kael s'assoit sur les ruines et cache son visage dans ses mains. "
        "Pas de douleur. Quelque chose de plus vieux que la douleur. "
        "Le soulagement d'une personne qui portait un poids depuis si "
        "longtemps qu'elle avait oublie ce que c'etait de marcher sans.\n\n"
        "Kratos pose une main sur son epaule. Kael ne dit rien. "
        "Ca n'a pas besoin d'etre dit.",
        'calm_ambient.mp3', 'fade', False, True, 'good'
    ),
    'b3_fin_neutre': (
        "Le Sceau est pose. Le verrou tient.\n\n"
        "Mais Kael disparait dans la nuit avant que les freres aient pu "
        "lui parler. Ils ne savent pas s'il est libre maintenant, ou "
        "simplement ailleurs.\n\n"
        "Dimos touche son cou. La marque est inerte. Il a le sentiment "
        "etrange d'une histoire qui n'est pas entierement finie - comme "
        "un livre dont on vient de refermer la derniere page, mais dont "
        "le dernier chapitre manque.\n\n"
        "Kratos le regarde. 'Ca va ?'\n"
        "'Je ne sais pas encore.' Dimos sourit malgre lui. 'Demande-moi "
        "dans un an.'\n\n"
        "Ils rentrent a Sparte. La route est longue. C'est bien comme ca.",
        'calm_ambient.mp3', 'continuous', False, True, 'neutral'
    ),
    'b3_fin_mauvaise': (
        "Kael a trahi.\n\n"
        "Au dernier moment, quand les fragments etaient presque en place, "
        "il a frappe - pas les freres. L'autel. Une fissure dans la pierre "
        "ancienne. Les fragments glissent dans les profondeurs.\n\n"
        "'Je suis desole,' dit-il. Et il a l'air de le penser vraiment. "
        "'Mais j'ai trop peur. J'ai toujours eu trop peur.'\n\n"
        "Il disparait.\n\n"
        "Les freres sont debout sur les ruines d'une chance perdue. "
        "La marque de Dimos brule rouge. Quelque chose en dessous respire.\n\n"
        "La peur de Kael a tout detruit. Mais sa peur n'etait pas "
        "sans raison. Peut-etre que la prochaine fois, il y a un chemin "
        "ou personne n'a besoin d'avoir autant peur.\n\n"
        "Recommencez. L'histoire peut etre differente.",
        'horror_intense.mp3', 'continuous', False, True, 'bad'
    ),

    # ── ACTE 3 — BRANCHE C : LA VERITE ──────────────────────────────────────
    'c3_apres_rituel': (
        "La salle du rituel est silencieuse.\n\n"
        "Dimos touche son cou. La marque est froide. Inerte. Il devrait "
        "se sentir vide - c'est ce qu'il attendait. Mais il se sent "
        "etrangement... complet.\n\n"
        "Kael est toujours la, debout dans un coin. 'Le verrou tient. "
        "Pour l'instant. Mais la marque peut se reactiver - une genese "
        "de cycle, pas une fin. La solution permanente est ailleurs.'\n"
        "'Ou ?' demande Kratos.\n"
        "'Dans l'origine de votre lignee. Votre pere savait. Il a laisse "
        "des traces.'\n\n"
        "Kael leur montre le chemin hors du Donjon. Il ne les suit pas. "
        "'Je ne peux pas vous aider plus que ca. Ce chemin, seuls les "
        "fils du destin peuvent le faire.'",
        'calm_ambient.mp3', 'fade', False, False, None
    ),
    'c3_archives': (
        "Les archives de Sparte. Un batiment que les freres ont passe "
        "devant toute leur vie sans jamais entrer.\n\n"
        "Ils cherchent pendant une nuit entiere. Le nom 'Deimos' n'existe "
        "pas dans les registres de naissance spartiales - mais il y a "
        "une entree sur un etranger arrive il y a dix-neuf ans, venant "
        "'des terres du nord', qui s'est marie avec une femme du village.\n\n"
        "Et une annotation dans la marge, en petite ecriture : "
        "'Voir aussi : Registres du Temple d'Athena. Lignee des Veilleurs.'\n\n"
        "'Les Veilleurs,' dit Dimos lentement. 'Pas les Gardiens du Verrou - "
        "les Veilleurs. C'est different.'\n"
        "Kratos fronce les sourcils. 'C'est quoi la difference ?'\n"
        "'Les Gardiens ferment. Les Veilleurs... regardent.'",
        'calm_ambient.mp3', 'continuous', False, False, None
    ),
    'c3_temple_athena': (
        "Le Temple d'Athena a Sparte. Lysara - si elle a ete liberee - "
        "les y attend. Sinon, la grande pretresse les recoit seule.\n\n"
        "Les Registres des Veilleurs. Un livre si vieux que les pages "
        "tombent en poussiere quand on les touche. Mais les mots sont "
        "encore lisibles.\n\n"
        "La lignee des Veilleurs n'est pas une lignee de guerriers. "
        "C'est une lignee de temoins. Des gens nes avec la capacite "
        "de voir les Dieux Oublies pour ce qu'ils sont - pas des "
        "monstres. Des forces naturelles qui ont ete emprisonnees par "
        "des dieux jaloux, pas parce qu'elles etaient mauvaises.\n\n"
        "'Alors... les Oublies ne sont pas mauvais ?' dit Dimos.\n"
        "'Ils sont... comme un fleuve qui deborde,' dit la pretresse. "
        "'Pas mauvais. Mais destructeurs si personne ne les guide.'",
        'calm_ambient.mp3', 'continuous', False, False, None
    ),
    'c3_cite_oubliee': (
        "La Cite Oubliee. Mais cette fois, les freres ne viennent pas "
        "sceller - ils viennent comprendre.\n\n"
        "Ils posent les mains sur l'autel au centre. La marque de Dimos "
        "s'eveille doucement - blanche, pas rouge. Et soudain ils voient.\n\n"
        "Les Dieux Oublies. Pas des monstres. Des ombres immenses, "
        "tristes, qui ont ete emprisonnees depuis si longtemps qu'elles "
        "ont oublie pourquoi elles etaient la.\n\n"
        "Et au centre de leur silence : quelque chose qui ressemble a "
        "une question.\n\n"
        "Dimos comprend avant son frere. 'Ils ne veulent pas se reveiller "
        "pour detruire. Ils veulent savoir si quelqu'un se souvient encore "
        "d'eux.'\n\n"
        "La reponse que Dimos donne ici changera tout.",
        'calm_ambient.mp3', 'fade', False, False, None
    ),
    'c3_fin_bonne': (
        "Dimos parle aux Oublies.\n\n"
        "Pas pour les repousser. Pour leur repondre.\n\n"
        "'Je me souviens de vous. Votre douleur est reelle. Votre "
        "emprisonnement etait injuste. Mais le monde d'en haut n'est "
        "pas pret pour vous. Pas encore. Restez encore. On apprendra "
        "a vous connaitre avant de vous liberer.'\n\n"
        "La marque sur son cou brille d'une lumiere blanche douce, "
        "puis s'eteint definitivement. Les Oublies se rendorment - "
        "non pas parce qu'ils sont forces, mais parce qu'ils ont "
        "ete entendus.\n\n"
        "Kratos regarde son frere avec quelque chose de nouveau dans "
        "les yeux. Pas la fierte du frere aine. Quelque chose de plus egal.\n\n"
        "Ils rentrent a Sparte, cote a cote, sous les etoiles de Grece.\n\n"
        "La marque ne reviendra plus. Pas dans cette generation.",
        'calm_ambient.mp3', 'fade', False, True, 'good'
    ),
    'c3_fin_neutre': (
        "Dimos essaie de parler aux Oublies.\n\n"
        "Mais les mots sont difficiles a trouver pour quelque chose "
        "d'aussi ancien. La marque pulse, hebetee, puis se stabilise.\n\n"
        "Les Oublies ne se rendorment pas completement. Mais ils ne "
        "se reveillent pas non plus. Un entre-deux fragile.\n\n"
        "Kael avait raison - ce n'est pas une fin. C'est une pause.\n\n"
        "'Il faudra revenir,' dit Dimos. 'Quand on saura mieux quoi dire.'\n"
        "'On reviendra,' dit Kratos.\n\n"
        "Ce n'est pas la victoire qu'ils esperaient. Mais c'est une "
        "victoire quand meme - celle de comprendre qu'il y avait une "
        "question a poser, et non une force a vaincre.",
        'calm_ambient.mp3', 'continuous', False, True, 'neutral'
    ),
    'c3_fin_mauvaise': (
        "Les mots manquent.\n\n"
        "Dimos essaie mais la peur prend le dessus au dernier moment - "
        "pas sa peur. La peur des Oublies. Quatre cents ans d'isolement "
        "qui se dechargent en un seul instant.\n\n"
        "La marque brule. Rouge. Chaude. Les freres tombent a genoux.\n\n"
        "L'autel se fissure. Quelque chose en dessous cesse de dormir.\n\n"
        "Kratos tire Dimos par le bras et ils courent. La Cite Oubliee "
        "s'effondre derriere eux.\n\n"
        "Ils ont compris trop de choses trop tard. Mais ils sont "
        "en vie. Et ils savent maintenant ce qu'il faut faire "
        "la prochaine fois - ecouter avant de parler, comprendre "
        "avant d'agir.\n\n"
        "L'histoire continue. Elle a toujours continue.",
        'horror_intense.mp3', 'continuous', False, True, 'bad'
    ),
}

# ---------------------------------------------------------------------------
# CHOICES
# (from_scene_key, choice_text, to_scene_key, order)
# ---------------------------------------------------------------------------
CHOICES_DATA = [

    # ── PROLOGUE ──────────────────────────────────────────────────────────
    ('prologue_matin',
     "Incarner Kratos - Le frere du milieu, impulsif et fort",
     'k1_jardin', 0),
    ('prologue_matin',
     "Incarner Dimos - Le plus jeune, curieux et agile",
     'd1_lisiere', 1),
    ('prologue_matin',
     "Incarner Optimus - L'aine, protecteur et courageux",
     'o1_avant_orage', 2),

    # ── ACTE 1 KRATOS ─────────────────────────────────────────────────────
    ('k1_jardin',
     "Se precipiter sur Optimus - voir s'il respire encore",
     'k1_optimus_blesse', 0),
    ('k1_jardin',
     "Ramasser le marteau et se lancer immediatement a la poursuite",
     'k1_foret', 1),

    ('k1_optimus_blesse',
     "Prendre le temps de fouiller la maison avant de partir",
     'k1_maison_secrets', 0),
    ('k1_optimus_blesse',
     "Partir immediatement - chaque seconde compte",
     'k1_foret', 1),

    ('k1_maison_secrets',
     "Prendre le Marteau d'Optimus - lourd mais puissant",
     'k1_foret', 0),
    ('k1_maison_secrets',
     "Prendre la vieille epee courte - plus legere et plus agile",
     'k1_foret', 1),

    ('k1_foret',
     "Liberer Theron et l'emmener - il connait peut-etre la route",
     'k1_campement', 0),
    ('k1_foret',
     "Le laisser enchaine - continuer seul avec juste ses informations",
     'k1_campement', 1),
    ('k1_foret',
     "Fouiller les poches de Theron avant de decider quoi que ce soit",
     'k1_theron_fouille', 2),

    ('k1_theron_fouille',
     "L'interroger - qui est-il vraiment ?",
     'k1_theron_interroge', 0),
    ('k1_theron_fouille',
     "Le laisser enchaine et partir en courant",
     'k1_campement', 1),

    ('k1_theron_interroge',
     "Le liberer et l'utiliser comme guide vers le Donjon",
     'k1_campement', 0),
    ('k1_theron_interroge',
     "Le liberer et le laisser partir - pas de confiance mais pas de mort",
     'k1_campement', 1),
    ('k1_theron_interroge',
     "Le laisser enchaine - qu'il decide de son sort",
     'k1_campement', 2),

    ('k1_campement',
     "Attaque frontale - charger en hurlant comme Optimus l'aurait fait",
     'k1_campement_combat', 0),
    ('k1_campement',
     "Contournement furtif - eviter le campement et continuer au nord",
     'k1_donjon_porte', 1),
    ('k1_campement',
     "Eteindre le feu depuis les arbres pour diviser les gardes",
     'k1_campement_combat', 2),

    ('k1_campement_combat',
     "Continuer vers le Donjon de Fer",
     'k1_donjon_porte', 0),
    ('k1_campement_combat',
     "Fouiller le campement d'abord - cle, carte, tout ce qui peut aider",
     'k1_donjon_porte', 1),

    ('k1_donjon_porte',
     "Entree principale - combattre les gardes ou utiliser la cle trouvee",
     'k1_fin_act1', 0),
    ('k1_donjon_porte',
     "Longer la falaise - chercher une entree secondaire ou des egouts",
     'k1_entree_egouts', 1),
    ('k1_donjon_porte',
     "Se deguiser avec l'armure d'un soldat vaincu au campement",
     'k1_fin_act1', 2),

    ('k1_entree_egouts',
     "Liberer Lysara et partir ensemble - elle guide, il protege",
     'k1_lysara', 0),
    ('k1_entree_egouts',
     "Prendre ses informations et continuer seul - la liberer apres",
     'k1_fin_act1', 1),

    ('k1_lysara',
     "Avancer ensemble - elle connait le plan, il combat",
     'k1_fin_act1', 0),
    ('k1_lysara',
     "La laisser en securite et aller seul avec ses informations",
     'k1_fin_act1', 1),

    ('k1_fin_act1',
     "Entrer dans les profondeurs du Donjon de Fer",
     'k2_entree_donjon', 0),

    # ── ACTE 1 DIMOS ──────────────────────────────────────────────────────
    ('d1_lisiere',
     "Observer ce qui se passe - tout prendre en memoire",
     'd1_chariot', 0),

    ('d1_chariot',
     "Faire semblant de dormir et ecouter la conversation des gardes",
     'd1_ecouter', 0),
    ('d1_chariot',
     "Chercher immediatement comment se liberer sans bruit",
     'd1_couteau', 1),

    ('d1_ecouter',
     "Continuer a faire semblant - attendre une opportunite parfaite",
     'd1_fuite_gue', 0),
    ('d1_ecouter',
     "Chercher discretement quelque chose dans la paille maintenant",
     'd1_couteau', 1),

    ('d1_couteau',
     "Couper les liens et attendre le bon moment pour sauter",
     'd1_fuite_gue', 0),
    ('d1_couteau',
     "Garder le couteau cache et ne pas se liberer encore",
     'd1_fuite_gue', 1),

    ('d1_fuite_gue',
     "Sauter du chariot maintenant - rouler dans les roseaux",
     'd1_foret_libre', 0),
    ('d1_fuite_gue',
     "Trop risque - attendre encore un peu",
     'd1_interrogatoire', 1),

    ('d1_interrogatoire',
     "Parler - simuler la peur et demander ou on l'emmene",
     'd1_foret_libre', 0),
    ('d1_interrogatoire',
     "Garder le silence total - observer le moindre detail",
     'd2_cellule_speciale', 1),

    ('d1_foret_libre',
     "S'approcher prudemment de la lumiere entre les arbres",
     'd1_berger', 0),
    ('d1_foret_libre',
     "Eviter la lumiere - toute lumiere ici pourrait etre un piege",
     'd1_choix_coeur', 1),

    ('d1_berger',
     "Dormir ici pour recuperer des forces - perdre du temps mais en gagner",
     'd1_choix_coeur', 0),
    ('d1_berger',
     "Repartir immediatement malgre la fatigue - le temps presse",
     'd1_choix_coeur', 1),

    ('d1_choix_coeur',
     "Courir vers Kratos - fuir ensemble hors de portee",
     'd1_fin_fuite_info', 0),
    ('d1_choix_coeur',
     "Se rendre volontairement - attirer tous les gardes et ouvrir la voie",
     'd1_fin_sacrifice', 1),
    ('d1_choix_coeur',
     "Crier a Kratos les informations sur la prophetie avant d'etre rattrapé",
     'd1_fin_fuite_info', 2),

    ('d1_fin_sacrifice',
     "Continuer - le Donjon de Fer vous attend",
     'd2_cellule_speciale', 0),
    ('d1_fin_fuite_info',
     "Rejoindre Kratos et entrer dans le Donjon ensemble",
     'k2_entree_donjon', 0),

    # ── ACTE 1 OPTIMUS ────────────────────────────────────────────────────
    ('o1_avant_orage',
     "Courir vers le cri de Dimos",
     'o1_charge', 0),

    ('o1_charge',
     "Lancer le marteau de toutes ses forces sur la tete du ravisseur",
     'o1_chute', 0),
    ('o1_charge',
     "Charger pour le tacker au niveau des jambes et le desequilibrer",
     'o1_chute', 1),
    ('o1_charge',
     "Frapper le bras qui tient Dimos - liberer son frere d'abord",
     'o1_chute', 2),

    ('o1_chute',
     "Tendre la main a Kratos et murmurer ses dernieres paroles",
     'o1_entredeux', 0),

    ('o1_entredeux',
     "Envoyer sa force a Kratos - il en aura besoin pour se battre",
     'o1_fin_force', 0),
    ('o1_entredeux',
     "Envoyer sa sagesse a Dimos - pour qu'il sache quoi dire au bon moment",
     'o1_fin_sagesse', 1),
    ('o1_entredeux',
     "Accepter le repos - ses freres n'ont besoin que d'eux-memes",
     'o1_fin_repos', 2),

    ('o1_fin_force',
     "Continuer l'histoire en tant que Kratos",
     'k1_jardin', 0),
    ('o1_fin_sagesse',
     "Continuer l'histoire en tant que Dimos",
     'd1_lisiere', 0),
    ('o1_fin_repos',
     "Rejouer depuis le debut et choisir un autre destin",
     'prologue_matin', 0),

    # ── ACTE 2 KRATOS ─────────────────────────────────────────────────────
    ('k2_entree_donjon',
     "Continuer sans s'attarder - trouver Dimos d'abord",
     'k2_salle_cinq_portes', 0),
    ('k2_entree_donjon',
     "Examiner les fresques - comprendre ce qui attend son frere",
     'k2_fresques_detail', 1),

    ('k2_fresques_detail',
     "Descendre plus profond dans le Donjon",
     'k2_salle_cinq_portes', 0),

    ('k2_salle_cinq_portes',
     "Poser les trois questions au gardien aux yeux blancs",
     'k2_gardien_lignee', 0),

    ('k2_gardien_lignee',
     "Prendre la porte de la Foudre - suivre son instinct",
     'k2_porte_foudre', 0),
    ('k2_gardien_lignee',
     "Prendre la porte du Feu - chercher une arme",
     'k2_forge_interdite', 1),
    ('k2_gardien_lignee',
     "Prendre la porte de l'Ombre directement - aller chercher Dimos",
     'k2_couloir_cellules', 2),

    ('k2_porte_foudre',
     "Liberer Zenos immediatement - il sera un allie",
     'k2_couloir_cellules', 0),
    ('k2_porte_foudre',
     "Obtenir ses informations et decider ensuite",
     'k2_couloir_cellules', 1),
    ('k2_porte_foudre',
     "Le laisser - chaque seconde perdue est dangereuse",
     'k2_couloir_cellules', 2),

    ('k2_forge_interdite',
     "Prendre les lames - elles semblent faites pour lui",
     'k2_couloir_cellules', 0),
    ('k2_forge_interdite',
     "Resister - le gardien a dit que ca changerait celui qui les porte",
     'k2_couloir_cellules', 1),
    ('k2_forge_interdite',
     "Examiner les lames d'abord - chercher des inscriptions",
     'k2_lames_inscription', 2),

    ('k2_lames_inscription',
     "Prendre les lames - il brule assez",
     'k2_couloir_cellules', 0),
    ('k2_lames_inscription',
     "Les laisser - il ne veut pas devenir quelque chose d'autre",
     'k2_couloir_cellules', 1),

    ('k2_couloir_cellules',
     "S'approcher de la cellule au fond d'ou vient la voix",
     'k2_reunion_freres', 0),

    ('k2_reunion_freres',
     "On parle de ca dehors - comment on sort d'ici maintenant ?",
     'k2_liberation', 0),
    ('k2_reunion_freres',
     "Echanger les informations d'abord - savoir tout avant d'agir",
     'k2_liberation', 1),

    ('k2_liberation',
     "Forcer les barreaux - brute force",
     'k2_alarme', 0),
    ('k2_liberation',
     "Utiliser la cle de geolier trouvee au campement",
     'k2_alarme', 1),
    ('k2_liberation',
     "Chercher un mecanisme - les barreaux rouilles ont peut-etre un point faible",
     'k2_alarme', 2),

    ('k2_alarme',
     "Combattre - tenir le couloir le temps que Dimos se mette a l'abri",
     'c2_retrouvailles', 0),
    ('k2_alarme',
     "Courir ensemble vers la salle du rituel - utiliser le puits d'aeration",
     'c2_retrouvailles', 1),
    ('k2_alarme',
     "Se cacher dans une cellule vide et laisser les gardes passer",
     'c2_retrouvailles', 2),

    # ── ACTE 2 DIMOS ──────────────────────────────────────────────────────
    ('d2_cellule_speciale',
     "Observer methodiquement la cellule et planifier une evasion",
     'd2_plan_evasion', 0),

    ('d2_plan_evasion',
     "Simuler une crise de panique - un enfant en detresse destabilise un garde",
     'd2_crise_panique', 0),
    ('d2_plan_evasion',
     "Attendre patiemment la releve et etudier le nouveau garde",
     'd2_kael_visite', 1),
    ('d2_plan_evasion',
     "Utiliser le couteau cache pour demonter le support du barreau",
     'd2_kael_visite', 2),

    ('d2_crise_panique',
     "Saisir la cle pendant que le garde repousse l'enfant en pleurs",
     'd2_kael_visite', 0),
    ('d2_crise_panique',
     "Le garde s'est mefie - echec, attendre une autre occasion",
     'd2_kael_visite', 1),

    ('d2_kael_visite',
     "Jouer l'ignorant - 'Non. Dis-moi.' Obtenir plus d'informations",
     'd2_kael_dialogue', 0),
    ('d2_kael_visite',
     "Montrer qu'on sait - 'Le frere marque. La cle d'une prophetie.'",
     'd2_kael_dialogue', 1),
    ('d2_kael_visite',
     "Garder le silence total et le fixer sans ciller",
     'd2_mira', 2),

    ('d2_kael_dialogue',
     "Ecouter jusqu'au bout ce que Kael a a dire",
     'd2_mira', 0),

    ('d2_mira',
     "Comment tu vas ? - priorite humaine avant strategie",
     'd2_marque_eveille', 0),
    ('d2_mira',
     "Tu as vu quelque chose d'utile depuis ta cellule ?",
     'd2_marque_eveille', 1),
    ('d2_mira',
     "Mon frere va venir. On va sortir tous les trois.",
     'd2_marque_eveille', 2),

    ('d2_marque_eveille',
     "Utiliser la fenetre de sept minutes pour aller vers Kratos",
     'c2_retrouvailles', 0),
    ('d2_marque_eveille',
     "Envoyer Mira vers Kratos et rester pour brouiller les pistes",
     'c2_retrouvailles', 1),
    ('d2_marque_eveille',
     "Attendre que Kratos arrive - il est plus proche qu'il n'y parait",
     'c2_retrouvailles', 2),

    # ── CONVERGENCE ACTE 2 ────────────────────────────────────────────────
    ('c2_retrouvailles',
     "Entrer dans la salle du rituel - affronter ce qui attend",
     'c2_salle_rituel', 0),

    ('c2_salle_rituel',
     "Attaquer immediatement sans ecouter",
     'c2_violence', 0),
    ('c2_salle_rituel',
     "Montre-nous ce que tu veux nous montrer - l'ecouter",
     'c2_kael_revele', 1),
    ('c2_salle_rituel',
     "Dimos s'avance - il y a une autre fin a la prophetie",
     'c2_dimos_parle', 2),

    ('c2_kael_revele',
     "Cette alliance est la seule logique - accepter le pacte",
     'c2_alliance', 0),
    ('c2_kael_revele',
     "Refuser le pacte - trouver les Gardiens sans lui",
     'a3_retour_sparte', 1),

    ('c2_dimos_parle',
     "Dimos effectue le rituel du Consentement",
     'c2_sacrifice_consenti', 0),

    ('c2_violence',
     "Ne pas le tuer - l'assommer et l'enchainer a sa propre table",
     'c2_kael_enchaine', 0),
    ('c2_violence',
     "Le tuer - finir ca maintenant",
     'c2_kael_tue', 1),

    # ── ACTE 3 BRANCHE A ──────────────────────────────────────────────────
    ('c2_kael_enchaine',
     "Rentrer a Sparte et trouver la deuxieme fin de la prophetie",
     'a3_retour_sparte', 0),

    ('a3_retour_sparte',
     "Ignorer les regards et courir directement vers la maison",
     'a3_maison_lettre', 0),
    ('a3_retour_sparte',
     "S'arreter et demander a un voisin ce qui s'est passe",
     'a3_maison_lettre', 1),
    ('a3_retour_sparte',
     "Observer en silence - lire la situation avant d'agir",
     'a3_maison_lettre', 2),

    ('a3_maison_lettre',
     "On sait. Continue. - montrer qu'on est pret a entendre tout",
     'a3_revelation_pere', 0),
    ('a3_maison_lettre',
     "Qui etait-il vraiment ? - la question directe",
     'a3_revelation_pere', 1),
    ('a3_maison_lettre',
     "Lire la lettre soi-meme en silence",
     'a3_revelation_pere', 2),

    ('a3_revelation_pere',
     "Partir vers Corinthe - trouver la pretresse qui connait les noms anciens",
     'a3_chemin_corinthe', 0),

    ('a3_chemin_corinthe',
     "Continuer vers Argos - trouver le forgeron qui garde la cle de lumiere",
     'a3_forgeron_argos', 0),

    ('a3_forgeron_argos',
     "Fuir immediatement vers la Cite Oubliee avant d'etre reperes",
     'a3_cite_oubliee', 0),
    ('a3_forgeron_argos',
     "Affronter les disciples ici pour les eliminer",
     'a3_cite_oubliee', 1),

    ('a3_cite_oubliee',
     "Poser les fragments sur l'autel - maintenant ou jamais",
     'a3_confrontation_finale', 0),
    ('a3_cite_oubliee',
     "Affronter Kael d'abord avant de s'approcher de l'autel",
     'a3_confrontation_finale', 1),

    ('a3_confrontation_finale',
     "Dimos pose les fragments - le verrou se referme",
     'a3_fin_bonne', 0),
    ('a3_confrontation_finale',
     "Kael perturbe le rituel - les fragments sont incomplets",
     'a3_fin_neutre', 1),
    ('a3_confrontation_finale',
     "Les disciples interviennent - le rituel echoue",
     'a3_fin_mauvaise', 2),

    # ── ACTE 3 BRANCHE B ──────────────────────────────────────────────────
    ('c2_alliance',
     "Accepter le pacte - marcher avec l'ennemi d'hier",
     'b3_pacte', 0),

    ('b3_pacte',
     "Partir avec Kael vers les Gardiens du Verrou",
     'b3_voyage', 0),

    ('b3_voyage',
     "Continuer le voyage malgre la mefiance",
     'b3_trahison', 0),

    ('b3_trahison',
     "Confronter Kael directement avec la tablette trouvee",
     'b3_cite_oubliee', 0),
    ('b3_trahison',
     "Attendre et surveiller - avoir la certitude avant d'agir",
     'b3_cite_oubliee', 1),
    ('b3_trahison',
     "Ignorer le message - lui faire confiance jusqu'au bout",
     'b3_cite_oubliee', 2),

    ('b3_cite_oubliee',
     "Poser les fragments avec Kael - ensemble",
     'b3_fin_bonne', 0),
    ('b3_cite_oubliee',
     "Poser les fragments seuls - sans attendre Kael",
     'b3_fin_neutre', 1),
    ('b3_cite_oubliee',
     "Kael trahit au dernier moment",
     'b3_fin_mauvaise', 2),

    # ── ACTE 3 BRANCHE C ──────────────────────────────────────────────────
    ('c2_sacrifice_consenti',
     "Comprendre l'origine - ce n'est pas fini",
     'c3_apres_rituel', 0),

    ('c3_apres_rituel',
     "Chercher dans les archives de Sparte - la lignee des Veilleurs",
     'c3_archives', 0),

    ('c3_archives',
     "Aller au Temple d'Athena - les Registres des Veilleurs",
     'c3_temple_athena', 0),

    ('c3_temple_athena',
     "Partir vers la Cite Oubliee - non pour sceller, mais pour comprendre",
     'c3_cite_oubliee', 0),

    ('c3_cite_oubliee',
     "Parler aux Oublies - repondre a leur question",
     'c3_fin_bonne', 0),
    ('c3_cite_oubliee',
     "Essayer de parler - les mots sont difficiles a trouver",
     'c3_fin_neutre', 1),
    ('c3_cite_oubliee',
     "La peur des Oublies vous submerge au dernier moment",
     'c3_fin_mauvaise', 2),
]


class Command(BaseCommand):
    help = 'Cree l\'histoire complete "Les Fils du Destin" (3 actes, 3 voies)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Supprime l\'histoire existante avant de la recreer'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING(
            '[VEH] Creation de "Les Fils du Destin"...'
        ))

        if options['reset']:
            Story.objects.filter(slug=SLUG).delete()
            self.stdout.write(self.style.WARNING('  Histoire existante supprimee.'))

        if Story.objects.filter(slug=SLUG).exists():
            self.stdout.write(self.style.WARNING(
                '  L\'histoire existe deja. Utilisez --reset pour la recreer.'
            ))
            return

        # 1. Creer l'histoire
        story = Story.objects.create(
            title='Les Fils du Destin',
            slug=SLUG,
            description=(
                'Sparte, dans les temps anciens. Un matin ordinaire bascule '
                'quand un colosse en armure noire emporte Dimos, le plus jeune '
                'des trois freres. Derriere cet enlevement : une prophetie '
                'vieille de quatre cents ans, une marque de naissance, et des '
                'dieux oublies qui n\'ont pas dit leur dernier mot.\n\n'
                'Choisissez votre voie : Kratos, Dimos, ou Optimus. '
                'Trois chemins. Une seule verite a decouvrir.'
            ),
            is_published=True,
        )
        self.stdout.write(f'  [OK] Histoire : {story.title}')

        # 2. Creer toutes les scenes
        scene_objects = {}
        for key, data in SCENES_DATA.items():
            narrative, music, transition, is_start, is_end, end_type = data
            scene = Scene.objects.create(
                story=story,
                scene_key=key,
                narrative=narrative,
                music_file=music,
                music_transition=transition,
                is_starting_scene=is_start,
                is_ending=is_end,
                ending_type=end_type,
            )
            scene_objects[key] = scene

        self.stdout.write(f'  [OK] {len(scene_objects)} scenes creees')

        # 3. Creer tous les choix
        total = 0
        errors = 0
        for from_key, text, to_key, order in CHOICES_DATA:
            if from_key not in scene_objects:
                self.stdout.write(
                    self.style.ERROR(f'  [ERR] Scene source manquante : {from_key}')
                )
                errors += 1
                continue
            if to_key not in scene_objects:
                self.stdout.write(
                    self.style.ERROR(f'  [ERR] Scene cible manquante : {to_key}')
                )
                errors += 1
                continue
            Choice.objects.create(
                scene=scene_objects[from_key],
                text=text,
                next_scene=scene_objects[to_key],
                order=order,
            )
            total += 1

        self.stdout.write(f'  [OK] {total} choix crees')
        if errors:
            self.stdout.write(self.style.ERROR(f'  [WARN] {errors} erreurs de reference'))

        # 4. Resume
        endings = sum(
            1 for _, d in SCENES_DATA.items() if d[4]
        )
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS(
            '  [SUCCESS] Les Fils du Destin cree avec succes !'
        ))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(f'  Scenes   : {len(scene_objects)} ({endings} fins)')
        self.stdout.write(f'  Choix    : {total}')
        self.stdout.write(f'  Voies    : Kratos / Dimos / Optimus (x3 actes)')
        self.stdout.write(f'  Branches : A (Course) / B (Quete) / C (Verite)')
        self.stdout.write(f'  URL      : /play/les-fils-du-destin/auto/')
        self.stdout.write('')
        self.stdout.write('  Lancer le serveur :')
        self.stdout.write(self.style.HTTP_INFO('  python manage.py runserver'))
