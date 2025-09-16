// Global state
let prompts = {};
let filteredPrompts = [];
let selectedPrompt = null;

// DOM elements
const searchInput = document.getElementById('searchInput');
const filterInput = document.getElementById('filterInput');
const loadingState = document.getElementById('loadingState');
const errorState = document.getElementById('errorState');
const emptyState = document.getElementById('emptyState');
const promptGroups = document.getElementById('promptGroups');
const promptDetail = document.getElementById('promptDetail');

// Stats elements
const totalPromptsEl = document.getElementById('totalPrompts');
const totalProjectsEl = document.getElementById('totalProjects');
const filteredResultsEl = document.getElementById('filteredResults');

// Detail elements
const detailTitle = document.getElementById('detailTitle');
const detailDescription = document.getElementById('detailDescription');
const detailTags = document.getElementById('detailTags');
const detailPrompt = document.getElementById('detailPrompt');
const detailMetadata = document.getElementById('detailMetadata');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  fetchPrompts();
  setupEventListeners();
});

function setupEventListeners() {
  searchInput.addEventListener('input', filterPrompts);
  filterInput.addEventListener('input', filterPrompts);
}

async function fetchPrompts() {
  try {
    showLoading();
    console.log('Fetching prompts from /api/prompts');
    
    const response = await fetch('/api/prompts');
    console.log('Response status:', response.status);
    
    if (!response.ok) {
      const text = await response.text();
      console.error('Response text:', text);
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const contentType = response.headers.get('content-type');
    console.log('Content-Type:', contentType);
    
    if (!contentType || !contentType.includes('application/json')) {
      const text = await response.text();
      console.error('Expected JSON but got:', text.substring(0, 200));
      throw new Error('Response is not JSON');
    }
    
    prompts = await response.json();
    console.log('Fetched prompts data:', prompts);
    
    filterPrompts();
    hideLoading();
  } catch (err) {
    console.error('Fetch error:', err);
    showError(err.message);
  }
}

function showLoading() {
  loadingState.style.display = 'flex';
  errorState.style.display = 'none';
  emptyState.style.display = 'none';
  promptGroups.style.display = 'none';
}

function hideLoading() {
  loadingState.style.display = 'none';
}

function showError(message) {
  loadingState.style.display = 'none';
  errorState.style.display = 'flex';
  emptyState.style.display = 'none';
  promptGroups.style.display = 'none';
  document.getElementById('errorMessage').textContent = message;
}

function showEmpty() {
  loadingState.style.display = 'none';
  errorState.style.display = 'none';
  emptyState.style.display = 'block';
  promptGroups.style.display = 'none';
}

function filterPrompts() {
  const searchTerm = searchInput.value.toLowerCase();
  const filterTerm = filterInput.value.toLowerCase();
  
  filteredPrompts = Object.values(prompts).filter(prompt => {
    const matchesSearch = prompt.prompt.toLowerCase().includes(searchTerm) ||
                         prompt.function_name.toLowerCase().includes(searchTerm) ||
                         (prompt.description || '').toLowerCase().includes(searchTerm);
    const matchesFilter = !filterTerm || prompt.function_name.toLowerCase().includes(filterTerm);
    return matchesSearch && matchesFilter;
  });
  
  updateStats();
  renderPrompts();
}

function updateStats() {
  totalPromptsEl.textContent = Object.keys(prompts).length;
  
  // Group by project
  const projectGroups = {};
  filteredPrompts.forEach(prompt => {
    const projectName = prompt.function_name.replace(/_\d+$/, '');
    const projectVersion = prompt.project_version || 'Unknown';
    const projectKey = `${projectName} v${projectVersion}`;
    
    if (!projectGroups[projectKey]) {
      projectGroups[projectKey] = [];
    }
    projectGroups[projectKey].push(prompt);
  });
  
  totalProjectsEl.textContent = Object.keys(projectGroups).length;
  filteredResultsEl.textContent = filteredPrompts.length;
}

function renderPrompts() {
  if (filteredPrompts.length === 0) {
    showEmpty();
    return;
  }
  
  loadingState.style.display = 'none';
  errorState.style.display = 'none';
  emptyState.style.display = 'none';
  promptGroups.style.display = 'block';
  
  // Group by project
  const projectGroups = {};
  filteredPrompts.forEach(prompt => {
    const projectName = prompt.function_name.replace(/_\d+$/, '');
    const projectVersion = prompt.project_version || 'Unknown';
    const projectKey = `${projectName} v${projectVersion}`;
    
    if (!projectGroups[projectKey]) {
      projectGroups[projectKey] = [];
    }
    projectGroups[projectKey].push(prompt);
  });
  
  // Sort project groups by version
  const sortedProjectKeys = Object.keys(projectGroups).sort((a, b) => {
    const extractVersion = (key) => {
      const match = key.match(/v(\d+\.\d+\.\d+)$/);
      if (!match) return [0, 0, 0];
      return match[1].split('.').map(Number);
    };
    
    const aVersion = extractVersion(a);
    const bVersion = extractVersion(b);
    
    for (let i = 0; i < 3; i++) {
      const aVal = aVersion[i] || 0;
      const bVal = bVersion[i] || 0;
      if (aVal !== bVal) return bVal - aVal;
    }
    return 0;
  });
  
  // Sort prompts within each project by agent version
  sortedProjectKeys.forEach(projectKey => {
    projectGroups[projectKey].sort((a, b) => {
      const aAgentVersion = a.agent_version || 0;
      const bAgentVersion = b.agent_version || 0;
      return bAgentVersion - aAgentVersion;
    });
  });
  
  // Render HTML
  promptGroups.innerHTML = sortedProjectKeys.map(projectKey => {
    const projectPrompts = projectGroups[projectKey];
    
    return `
      <div class="function-group">
        <h2 class="function-name">${projectKey}</h2>
        <div class="prompt-grid">
          ${projectPrompts.map(prompt => `
            <div class="prompt-card" onclick="selectPrompt('${prompt.function_name}_${prompt.version}')">
              <div class="prompt-header">
                <span class="version-badge">v${prompt.agent_version}</span>
                <span class="function-name-badge">${prompt.function_name}</span>
              </div>
              <p class="description">${prompt.description || 'No description'}</p>
              <div class="tags">
                ${(prompt.tags || []).map(tag => `<span class="tag">${tag}</span>`).join('')}
              </div>
              <div class="prompt-preview">
                ${prompt.prompt.length > 100 ? prompt.prompt.substring(0, 100) + '...' : prompt.prompt}
              </div>
              <div class="created-at">
                ${new Date(prompt.created_at).toLocaleDateString()}
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }).join('');
}

function selectPrompt(promptKey) {
  selectedPrompt = prompts[promptKey];
  if (!selectedPrompt) return;
  
  // Update detail panel
  detailTitle.textContent = `${selectedPrompt.function_name} v${selectedPrompt.agent_version}`;
  detailDescription.textContent = selectedPrompt.description || 'No description provided';
  
  // Update tags
  if (selectedPrompt.tags && selectedPrompt.tags.length > 0) {
    detailTags.innerHTML = selectedPrompt.tags.map(tag => `<span class="tag">${tag}</span>`).join('');
  } else {
    detailTags.innerHTML = '<span class="no-tags">No tags</span>';
  }
  
  // Update prompt
  detailPrompt.textContent = selectedPrompt.prompt;
  
  // Update metadata
  detailMetadata.innerHTML = `
    <div class="meta-item">
      <strong>Project Version:</strong> ${selectedPrompt.project_version}
    </div>
    <div class="meta-item">
      <strong>Agent Version:</strong> ${selectedPrompt.agent_version}
    </div>
    <div class="meta-item">
      <strong>Created:</strong> ${new Date(selectedPrompt.created_at).toLocaleString()}
    </div>
  `;
  
  // Show detail panel
  promptDetail.style.display = 'block';
  
  // Update selected state
  document.querySelectorAll('.prompt-card').forEach(card => {
    card.classList.remove('selected');
  });
  event.currentTarget.classList.add('selected');
}

function closeDetail() {
  promptDetail.style.display = 'none';
  selectedPrompt = null;
  
  // Remove selected state
  document.querySelectorAll('.prompt-card').forEach(card => {
    card.classList.remove('selected');
  });
}
