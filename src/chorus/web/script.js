// Global state
let prompts = {};
let projects = {};
let selectedProject = null;

// DOM elements
const searchInput = document.getElementById('searchInput');
const loadingState = document.getElementById('loadingState');
const errorState = document.getElementById('errorState');
const emptyState = document.getElementById('emptyState');
const projectGrid = document.getElementById('projectGrid');
const projectDetail = document.getElementById('projectDetail');

// Stats elements
const totalPromptsEl = document.getElementById('totalPrompts');
const totalProjectsEl = document.getElementById('totalProjects');
const filteredResultsEl = document.getElementById('filteredResults');

// Project detail elements
const projectTitle = document.getElementById('projectTitle');
const totalAgents = document.getElementById('totalAgents');
const latestVersion = document.getElementById('latestVersion');
const agentsList = document.getElementById('agentsList');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  fetchPrompts();
  setupEventListeners();
});

function setupEventListeners() {
  searchInput.addEventListener('input', filterProjects);
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
    
    processProjects();
    filterProjects();
    hideLoading();
  } catch (err) {
    console.error('Fetch error:', err);
    showError(err.message);
  }
}

function processProjects() {
  projects = {};
  
  // Group prompts by project
  Object.values(prompts).forEach(prompt => {
    // Only include prompts that have a project_version
    if (!prompt.project_version) {
      return; // Skip prompts without project assignment
    }
    
    const projectKey = prompt.project_version;
    
    if (!projects[projectKey]) {
      projects[projectKey] = {
        version: prompt.project_version,
        agents: [],
        totalAgents: 0,
        latestAgentVersion: 0,
        allTags: new Set(),
        allDescriptions: []
      };
    }
    
    // Add agent to project
    projects[projectKey].agents.push(prompt);
    projects[projectKey].totalAgents++;
    projects[projectKey].latestAgentVersion = Math.max(
      projects[projectKey].latestAgentVersion, 
      prompt.agent_version || 0
    );
    
    // Collect tags and descriptions
    if (prompt.tags) {
      prompt.tags.forEach(tag => projects[projectKey].allTags.add(tag));
    }
    if (prompt.description) {
      projects[projectKey].allDescriptions.push(prompt.description);
    }
  });
  
  // Convert Set to Array for tags
  Object.values(projects).forEach(project => {
    project.allTags = Array.from(project.allTags);
  });
  
  console.log('Processed projects:', projects);
}

function showLoading() {
  loadingState.style.display = 'flex';
  errorState.style.display = 'none';
  emptyState.style.display = 'none';
  projectGrid.style.display = 'none';
}

function hideLoading() {
  loadingState.style.display = 'none';
}

function showError(message) {
  loadingState.style.display = 'none';
  errorState.style.display = 'flex';
  emptyState.style.display = 'none';
  projectGrid.style.display = 'none';
  document.getElementById('errorMessage').textContent = message;
}

function showEmpty() {
  loadingState.style.display = 'none';
  errorState.style.display = 'none';
  emptyState.style.display = 'block';
  projectGrid.style.display = 'none';
}

function filterProjects() {
  const searchTerm = searchInput.value.toLowerCase();
  
  const filteredProjects = Object.entries(projects).filter(([projectKey, project]) => {
    const matchesSearch = projectKey.toLowerCase().includes(searchTerm) ||
                         project.allDescriptions.some(desc => desc.toLowerCase().includes(searchTerm)) ||
                         project.allTags.some(tag => tag.toLowerCase().includes(searchTerm));
    return matchesSearch;
  });
  
  updateStats(filteredProjects);
  renderProjects(filteredProjects);
}

function updateStats(filteredProjects) {
  const totalPromptsCount = Object.values(prompts).length;
  const totalProjectsCount = Object.keys(projects).length;
  const filteredCount = filteredProjects.length;
  
  totalPromptsEl.textContent = totalPromptsCount;
  totalProjectsEl.textContent = totalProjectsCount;
  filteredResultsEl.textContent = filteredCount;
}

function renderProjects(projectsToRender) {
  if (projectsToRender.length === 0) {
    showEmpty();
    return;
  }
  
  loadingState.style.display = 'none';
  errorState.style.display = 'none';
  emptyState.style.display = 'none';
  projectGrid.style.display = 'grid';
  
  // Sort projects by version (newest first)
  projectsToRender.sort(([aKey, aProject], [bKey, bProject]) => {
    const aVersion = parseVersion(aProject.version);
    const bVersion = parseVersion(bProject.version);
    
    for (let i = 0; i < 3; i++) {
      const aVal = aVersion[i] || 0;
      const bVal = bVersion[i] || 0;
      if (aVal !== bVal) return bVal - aVal;
    }
    return 0;
  });
  
  // Render HTML
  projectGrid.innerHTML = projectsToRender.map(([projectKey, project]) => {
    const description = project.allDescriptions[0] || 'No description available';
    const tags = project.allTags.slice(0, 3); // Show first 3 tags
    
    return `
      <div class="project-card" onclick="selectProject('${projectKey}')">
        <div class="project-header">
          <div class="project-name">Project ${projectKey}</div>
          <div class="project-version">v${project.version}</div>
        </div>
        <div class="project-stats">
          <div class="project-stat">
            <span class="project-stat-value">${project.totalAgents}</span>
            <span class="project-stat-label">Agents</span>
          </div>
          <div class="project-stat">
            <span class="project-stat-value">v${project.latestAgentVersion}</span>
            <span class="project-stat-label">Latest</span>
          </div>
        </div>
        <div class="project-description">${description}</div>
        <div class="project-tags">
          ${tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
        </div>
      </div>
    `;
  }).join('');
}

function parseVersion(version) {
  if (!version) return [0, 0, 0];
  return version.split('.').map(Number).concat([0, 0, 0]).slice(0, 3);
}

function selectProject(projectKey) {
  selectedProject = projects[projectKey];
  if (!selectedProject) return;
  
  // Update project detail panel
  projectTitle.textContent = `Project ${projectKey}`;
  totalAgents.textContent = selectedProject.totalAgents;
  latestVersion.textContent = `v${selectedProject.latestAgentVersion}`;
  
  // Sort agents by version (newest first)
  const sortedAgents = selectedProject.agents.sort((a, b) => {
    const aVersion = a.agent_version || 0;
    const bVersion = b.agent_version || 0;
    return bVersion - aVersion;
  });
  
  // Render agents list
  agentsList.innerHTML = sortedAgents.map(agent => `
    <div class="agent-item" onclick="showAgentDetail('${agent.function_name}_${agent.version}')">
      <div class="agent-header">
        <span class="agent-name">${agent.function_name}</span>
        <span class="agent-version">v${agent.agent_version}</span>
      </div>
      <div class="agent-description">${agent.description || 'No description'}</div>
    </div>
  `).join('');
  
  // Show project detail panel
  projectDetail.style.display = 'block';
  
  // Update selected state
  document.querySelectorAll('.project-card').forEach(card => {
    card.classList.remove('selected');
  });
  event.currentTarget.classList.add('selected');
}

function showAgentDetail(agentKey) {
  const agent = prompts[agentKey];
  if (!agent) return;
  
  // For now, just show an alert with agent details
  // You could expand this to show a modal or another detail view
  alert(`Agent: ${agent.function_name}\nVersion: v${agent.agent_version}\nDescription: ${agent.description || 'No description'}\n\nPrompt:\n${agent.prompt.substring(0, 200)}...`);
}

function closeProjectDetail() {
  projectDetail.style.display = 'none';
  selectedProject = null;
  
  // Remove selected state
  document.querySelectorAll('.project-card').forEach(card => {
    card.classList.remove('selected');
  });
}