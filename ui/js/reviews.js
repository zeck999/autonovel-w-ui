/**
    ui/js/reviews.js — Current Review button and modal component for Autonovel Web UI
 */

import { api } from './api.js';

export function initReviews() {
    const reviewBtn = document.getElementById('current-review-btn');
    const reviewModal = document.getElementById('review-modal');
    const reviewModalClose = document.getElementById('review-modal-close');
    const reviewModalBody = document.getElementById('review-modal-body');

    if (!reviewBtn || !reviewModal) return;

    let currentReviewData = null;

    async function fetchReviewStatus() {
        try {
            const data = await api.getLatestReview();
            currentReviewData = data;
            
            if (data && data.exists !== false && (data.stars !== undefined || data.title)) {
                const stars = data.stars !== undefined ? data.stars : 'N/A';
                reviewBtn.innerHTML = `<span class="review-icon">★</span> <span class="review-text">Revue: ${stars}</span>`;
                if (data.file_path) {
                    reviewBtn.title = `Source: ${data.file_path} (Timestamp: ${data.timestamp || 'N/A'})`;
                } else {
                    reviewBtn.title = 'Current manuscript review status';
                }
                reviewBtn.classList.add('has-review');
            } else {
                reviewBtn.innerHTML = `<span class="review-icon">☆</span> <span class="review-text">Non évalué</span>`;
                reviewBtn.title = 'No review logs found. Click to evaluate.';
                reviewBtn.classList.remove('has-review');
            }
        } catch (err) {
            console.error('Failed to fetch latest review:', err);
            reviewBtn.innerHTML = `<span class="review-icon">⚠</span> <span class="review-text">Erreur revue</span>`;
            reviewBtn.title = 'Failed to load review status';
        }
    }

    function renderModalContent(data) {
        if (!data || data.exists === false) {
            return `
                <div class="empty-state">
                    <h3>Aucune revue disponible</h3>
                    <p>${data?.message || 'Aucun journal de revue n\'a été trouvé dans edit_logs/.'}</p>
                    <button class="btn btn-primary" id="trigger-eval-btn" style="margin-top: 1rem;">Lancer une évaluation</button>
                </div>
            `;
        }

        const stars = data.stars !== undefined ? data.stars : 'N/A';
        const title = data.title || 'Manuscrit Autonovel';
        const timestamp = data.timestamp || 'Inconnu';
        const filePath = data.file_path || 'edit_logs/...';
        const summary = data.critic_summary || 'Aucun résumé disponible.';
        const professorItems = data.professor_items || [];

        let itemsHtml = '';
        if (professorItems.length === 0) {
            itemsHtml = '<p class="text-muted">Aucune suggestion critique enregistrée.</p>';
        } else {
            itemsHtml = professorItems.map(item => `
                <div class="review-item-card ${item.qualified ? 'qualified' : ''}">
                    <div class="review-item-header">
                        <span class="badge ${item.severity === 'major' ? 'badge-danger' : 'badge'}">#${item.number || '?'} — ${escapeHtml(item.title || 'Suggestion')}</span>
                        <span class="badge">${escapeHtml(item.severity || 'normal')} / ${escapeHtml(item.type || 'craft')}</span>
                        ${item.qualified ? '<span class="badge badge-success">Qualifié</span>' : ''}
                    </div>
                    <p class="review-item-suggestion"><strong>Suggestion :</strong> ${escapeHtml(item.suggestion || item.full_text || '')}</p>
                </div>
            `).join('');
        }

        return `
            <div class="review-summary-header">
                <div class="review-meta-line"><strong>Titre :</strong> ${escapeHtml(title)}</div>
                <div class="review-meta-line"><strong>Note / Étoiles :</strong> <span class="star-rating">★ ${stars} / 5</span></div>
                <div class="review-meta-line"><strong>Horodatage :</strong> ${escapeHtml(timestamp)}</div>
                <div class="review-meta-line"><strong>Fichier source :</strong> <code>${escapeHtml(filePath)}</code></div>
                <div class="review-meta-line"><strong>Critères :</strong> Total: ${data.total_items || 0} | Majeurs: ${data.major_items || 0} | Qualifiés: ${data.qualified_items || 0}</div>
            </div>

            <div class="review-section">
                <h4 class="form-label" style="margin-top: 1.25rem;">Résumé du Critique Littéraire</h4>
                <div class="critic-summary-box">${escapeHtml(summary)}</div>
            </div>

            <div class="review-section">
                <h4 class="form-label" style="margin-top: 1.25rem;">Suggestions du Professeur de Craft (${professorItems.length})</h4>
                <div class="professor-items-list">${itemsHtml}</div>
            </div>
        `;
    }

    function openModal() {
        reviewModal.classList.add('open');
        reviewModalBody.innerHTML = '<div class="empty-state"><p>Chargement des détails de la revue...</p></div>';
        
        api.getLatestReview().then(data => {
            currentReviewData = data;
            reviewModalBody.innerHTML = renderModalContent(data);
            
            const evalBtn = document.getElementById('trigger-eval-btn');
            if (evalBtn) {
                evalBtn.addEventListener('click', async () => {
                    evalBtn.textContent = 'Évaluation en cours...';
                    evalBtn.disabled = true;
                    try {
                        await api.evaluateProject({});
                        const freshData = await api.getLatestReview();
                        currentReviewData = freshData;
                        reviewModalBody.innerHTML = renderModalContent(freshData);
                        fetchReviewStatus();
                    } catch (e) {
                        alert('Échec de l\'évaluation: ' + e.message);
                        evalBtn.textContent = 'Lancer une évaluation';
                        evalBtn.disabled = false;
                    }
                });
            }
        }).catch(err => {
            reviewModalBody.innerHTML = `<div class="empty-state"><p class="text-danger">Erreur de chargement: ${escapeHtml(err.message)}</p></div>`;
        });
    }

    function closeModal() {
        reviewModal.classList.remove('open');
    }

    reviewBtn.addEventListener('click', openModal);
    if (reviewModalClose) reviewModalClose.addEventListener('click', closeModal);

    reviewModal.addEventListener('click', (e) => {
        if (e.target === reviewModal) {
            closeModal();
        }
    });

    window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && reviewModal.classList.contains('open')) {
            closeModal();
        }
    });

    fetchReviewStatus();
    setInterval(fetchReviewStatus, 30000);
}

function escapeHtml(str) {
    return String(str || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
