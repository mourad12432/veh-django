/**
 * VEH — Logique auxiliaire des choix.
 * Gère l'animation de survol et les raccourcis clavier (1, 2, 3).
 */

'use strict';

document.addEventListener('DOMContentLoaded', () => {

    const choiceForms = document.querySelectorAll('.choice-form');

    // ── Raccourcis clavier : touche 1, 2 ou 3 ──────────────
    document.addEventListener('keydown', (e) => {
        const key = parseInt(e.key);
        if (key >= 1 && key <= choiceForms.length) {
            const form = choiceForms[key - 1];
            if (form) {
                const btn = form.querySelector('button');
                // Simuler un clic visuel
                btn.classList.add('scale-95', 'brightness-125');
                setTimeout(() => {
                    btn.classList.remove('scale-95', 'brightness-125');
                    form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
                }, 150);
            }
        }
    });

    // ── Indicateur de raccourci clavier dans les boutons ───
    choiceForms.forEach((form, index) => {
        const letter = form.querySelector('.choice-letter');
        if (letter) {
            letter.setAttribute('title', `Raccourci : touche ${index + 1}`);
        }
    });
});
