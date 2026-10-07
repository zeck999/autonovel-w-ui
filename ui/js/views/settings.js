/**
    ui/js/views/settings.js — Settings view component for AI API keys and configuration
 */

import { api } from '../api.js';

export async function renderSettings(container) {
    container.innerHTML = `
        <div class="view-header">
            <h2>Paramètres & Clés API IA</h2>
            <p>Gérez vos clés API sécurisées pour Anthropic, ElevenLabs et Fal.ai.</p>
        </div>

        <div class="card" style="max-width: 800px; margin: 0 auto; padding: 2rem;">
            <div id="settings-loading" style="text-align: center; color: #888;">Chargement des paramètres...</div>
            <form id="settings-form" style="display: none;">
                <div class="form-group" style="margin-bottom: 1.5rem;">
                    <label style="display: block; font-weight: 600; margin-bottom: 0.5rem;">ANTHROPIC_API_KEY (Claude)</label>
                    <div style="display: flex; gap: 0.5rem;">
                        <input type="password" id="input-anthropic" class="form-control" style="flex: 1; padding: 0.5rem; background: #1a1915; border: 1px solid #333; color: #eee; border-radius: 4px;" placeholder="sk-ant-...">
                        <button type="button" class="btn btn-sm" id="test-anthropic">Tester</button>
                    </div>
                    <small id="status-anthropic" style="color: #888; display: block; margin-top: 0.25rem;"></small>
                </div>

                <div class="form-group" style="margin-bottom: 1.5rem;">
                    <label style="display: block; font-weight: 600; margin-bottom: 0.5rem;">ELEVENLABS_API_KEY (Audio)</label>
                    <div style="display: flex; gap: 0.5rem;">
                        <input type="password" id="input-elevenlabs" class="form-control" style="flex: 1; padding: 0.5rem; background: #1a1915; border: 1px solid #333; color: #eee; border-radius: 4px;" placeholder="ElevenLabs API Key">
                        <button type="button" class="btn btn-sm" id="test-elevenlabs">Tester</button>
                    </div>
                    <small id="status-elevenlabs" style="color: #888; display: block; margin-top: 0.25rem;"></small>
                </div>

                <div class="form-group" style="margin-bottom: 2rem;">
                    <label style="display: block; font-weight: 600; margin-bottom: 0.5rem;">FAL_KEY (Images / Nano Banana)</label>
                    <div style="display: flex; gap: 0.5rem;">
                        <input type="password" id="input-fal" class="form-control" style="flex: 1; padding: 0.5rem; background: #1a1915; border: 1px solid #333; color: #eee; border-radius: 4px;" placeholder="Fal.ai Key">
                        <button type="button" class="btn btn-sm" id="test-fal">Tester</button>
                    </div>
                    <small id="status-fal" style="color: #888; display: block; margin-top: 0.25rem;"></small>
                </div>

                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <button type="submit" class="btn btn-primary" id="save-settings">Enregistrer les clés</button>
                    <span id="settings-message" style="font-weight: 500;"></span>
                </div>
            </form>
        </div>
    `;

    try {
        const keysStatus = await api.getSettingsKeys();
        document.getElementById('settings-loading').style.display = 'none';
        document.getElementById('settings-form').style.display = 'block';

        const anthropicInput = document.getElementById('input-anthropic');
        const elevenlabsInput = document.getElementById('input-elevenlabs');
        const falInput = document.getElementById('input-fal');

        const anthropicStatus = document.getElementById('status-anthropic');
        const elevenlabsStatus = document.getElementById('status-elevenlabs');
        const falStatus = document.getElementById('status-fal');

        if (keysStatus.ANTHROPIC_API_KEY?.configured) {
            anthropicInput.placeholder = `Configuré (${keysStatus.ANTHROPIC_API_KEY.masked_value})`;
            anthropicStatus.textContent = `Actuellement configuré (${keysStatus.ANTHROPIC_API_KEY.masked_value})`;
            anthropicStatus.style.color = '#4ade80';
        } else {
            anthropicStatus.textContent = 'Non configuré';
        }

        if (keysStatus.ELEVENLABS_API_KEY?.configured) {
            elevenlabsInput.placeholder = `Configuré (${keysStatus.ELEVENLABS_API_KEY.masked_value})`;
            elevenlabsStatus.textContent = `Actuellement configuré (${keysStatus.ELEVENLABS_API_KEY.masked_value})`;
            elevenlabsStatus.style.color = '#4ade80';
        } else {
            elevenlabsStatus.textContent = 'Non configuré';
        }

        if (keysStatus.FAL_KEY?.configured) {
            falInput.placeholder = `Configuré (${keysStatus.FAL_KEY.masked_value})`;
            falStatus.textContent = `Actuellement configuré (${keysStatus.FAL_KEY.masked_value})`;
            falStatus.style.color = '#4ade80';
        } else {
            falStatus.textContent = 'Non configuré';
        }

        async function handleTest(provider, inputId, statusElId) {
            const val = document.getElementById(inputId).value.trim();
            const statusEl = document.getElementById(statusElId);
            statusEl.textContent = 'Test en cours...';
            statusEl.style.color = '#fbbf24';
            try {
                const res = await api.testSettingsKey({ provider, api_key: val || undefined });
                if (res.success) {
                    statusEl.textContent = `✓ ${res.message} (${res.latency_ms}ms)`;
                    statusEl.style.color = '#4ade80';
                } else {
                    statusEl.textContent = `✗ ${res.message}`;
                    statusEl.style.color = '#f87171';
                }
            } catch (err) {
                statusEl.textContent = `✗ Erreur de test : ${err.message}`;
                statusEl.style.color = '#f87171';
            }
        }

        document.getElementById('test-anthropic').addEventListener('click', () => handleTest('anthropic', 'input-anthropic', 'status-anthropic'));
        document.getElementById('test-elevenlabs').addEventListener('click', () => handleTest('elevenlabs', 'input-elevenlabs', 'status-elevenlabs'));
        document.getElementById('test-fal').addEventListener('click', () => handleTest('fal', 'input-fal', 'status-fal'));

        document.getElementById('settings-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const msgEl = document.getElementById('settings-message');
            msgEl.textContent = 'Enregistrement...';
            msgEl.style.color = '#fbbf24';

            const payload = {};
            const anthVal = anthropicInput.value.trim();
            const elevVal = elevenlabsInput.value.trim();
            const falVal = falInput.value.trim();

            if (anthVal) payload.anthropic_api_key = anthVal;
            if (elevVal) payload.elevenlabs_api_key = elevVal;
            if (falVal) payload.fal_key = falVal;

            try {
                await api.updateSettingsKeys(payload);
                msgEl.textContent = '✓ Clés enregistrées avec succès !';
                msgEl.style.color = '#4ade80';
                anthropicInput.value = '';
                elevenlabsInput.value = '';
                falInput.value = '';
                setTimeout(() => { msgEl.textContent = ''; }, 4000);
            } catch (err) {
                msgEl.textContent = `✗ Erreur : ${err.message}`;
                msgEl.style.color = '#f87171';
            }
        });

    } catch (err) {
        document.getElementById('settings-loading').textContent = `Erreur de chargement : ${err.message}`;
        document.getElementById('settings-loading').style.color = '#f87171';
    }
}
