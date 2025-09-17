// Global state
let runs = [];
let selectedProject = null;
let selectedVersion = null;

// DOM elements
const searchInput = document.getElementById('searchInput');
const loadingState = document.getElementById('loadingState');
const errorState = document.getElementById('errorState');
const emptyState = document.getElementById('emptyState');

// Views
const projectsView = document.getElementById('projectsView');
const versionsView = document.getElementById('versionsView');
const agentsView = document.getElementById('agentsView');
const agentSidebar = document.getElementById('agentSidebar');

// Grids/Lists
const projectsGrid = document.getElementById('projectsGrid');
const versionsList = document.getElementById('versionsList');
const agentsList = document.getElementById('agentsList');

// View headers
const versionsProjectTitle = document.getElementById('versionsProjectTitle');
const agentsVersionTitle = document.getElementById('agentsVersionTitle');

// Agent modal elements
const agentTitle = document.getElementById('agentTitle');
const agentName = document.getElementById('agentName');
const agentVersion = document.getElementById('agentVersion');
const agentCreated = document.getElementById('agentCreated');
const agentExecutionTime = document.getElementById('agentExecutionTime');
const agentPrompt = document.getElementById('agentPrompt');
const agentSystem = document.getElementById('agentSystem');
const agentInputs = document.getElementById('agentInputs');
const agentOutput = document.getElementById('agentOutput');

// Stats elements
const totalPromptsEl = document.getElementById('totalPrompts');
const totalProjectsEl = document.getElementById('totalProjects');
const statsSection = document.querySelector('.stats');
const controlsSection = document.querySelector('.controls');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  fetchRuns();
  setupEventListeners();
});

function setupEventListeners() {
  searchInput.addEventListener('input', filterProjects);
}

async function fetchRuns() {
  try {
    showLoading();
    console.log('Fetching runs from /api/runs');
    
    const response = await fetch('/api/runs');
    console.log('Response status:', response.status);
    
    if (!response.ok) {
      const text = await response.text();
      console.error('Response text:', text);
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    
    runs = data.runs || [];
    displayProjects();
    updateStats();
    
  } catch (error) {
    console.error('Error fetching runs:', error);
    showError('Failed to load runs: ' + error.message);
  }
}

function showLoading() {
  loadingState.style.display = 'block';
  errorState.style.display = 'none';
  emptyState.style.display = 'none';
  showView('projects');
}

function showError(message) {
  loadingState.style.display = 'none';
  errorState.style.display = 'block';
  emptyState.style.display = 'none';
  document.getElementById('errorMessage').textContent = message;
}

function showEmpty() {
  loadingState.style.display = 'none';
  errorState.style.display = 'none';
  emptyState.style.display = 'block';
}

function showView(viewName) {
  // Hide all views
  projectsView.style.display = 'none';
  versionsView.style.display = 'none';
  agentsView.style.display = 'none';
  agentSidebar.style.display = 'none';
  
  // Show/hide stats and controls based on view
  if (viewName === 'projects') {
    statsSection.style.display = 'flex';
    controlsSection.style.display = 'flex';
  } else {
    statsSection.style.display = 'none';
    controlsSection.style.display = 'none';
  }
  
  // Show selected view
  switch(viewName) {
    case 'projects':
      projectsView.style.display = 'block';
      break;
    case 'versions':
      versionsView.style.display = 'block';
      break;
    case 'agents':
      agentsView.style.display = 'block';
      break;
    case 'sidebar':
      agentSidebar.style.display = 'block';
      break;
  }
}

function displayProjects() {
  if (runs.length === 0) {
    showEmpty();
    return;
  }
  
  loadingState.style.display = 'none';
  errorState.style.display = 'none';
  emptyState.style.display = 'none';
  
  // Group runs by project name
  const projects = {};
  runs.forEach(run => {
    if (!projects[run.system_name]) {
      projects[run.system_name] = {
        name: run.system_name,
        versions: [],
        totalPrompts: 0
      };
    }
    projects[run.system_name].versions.push(run);
    projects[run.system_name].totalPrompts += run.total_prompts;
  });
  
  // Sort versions by creation date (newest first)
  Object.values(projects).forEach(project => {
    project.versions.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
  });
  
  // Display project cards
  projectsGrid.innerHTML = '';
  Object.values(projects).forEach(project => {
    const latestVersion = project.versions[0];
    const projectCard = createProjectCard(project, latestVersion);
    projectsGrid.appendChild(projectCard);
  });
}

function createProjectCard(project, latestVersion) {
  const card = document.createElement('div');
  card.className = 'project-card';
  card.onclick = () => openProject(project);
  
  card.innerHTML = `
    <div class="project-name">${project.name}</div>
    <div class="project-version">Latest: v${latestVersion.project_version}</div>
    <div class="project-stats">
      <span>${project.versions.length} versions</span>
      <span>${project.totalPrompts} prompts</span>
    </div>
  `;
  
  return card;
}

function openProject(project) {
  selectedProject = project;
  versionsProjectTitle.textContent = `${project.name} - Versions`;
  displayVersions(project.versions);
  showView('versions');
}

function displayVersions(versions) {
  versionsList.innerHTML = '';
  
  versions.forEach((version, index) => {
    const versionCard = createVersionCard(version, index);
    versionsList.appendChild(versionCard);
  });
}

function createVersionCard(version, index) {
  const card = document.createElement('div');
  card.className = 'version-card';
  card.onclick = () => openVersion(version);
  
  const agents = getAgentsForVersion(version);
  const isLatest = index === 0;
  
  // Create agent name bubbles
  const agentBubbles = agents.map(agent => 
    `<span class="agent-bubble">${agent.name}</span>`
  ).join('');
  
  card.innerHTML = `
    <div class="version-header">
      <div class="version-title">
        ${isLatest ? 'Latest Version' : `Version ${version.project_version}`}
        ${isLatest ? '<span class="latest-badge">Latest</span>' : ''}
      </div>
      <div class="version-date">${new Date(version.created_at).toLocaleDateString()}</div>
    </div>
    <div class="version-agents">
      <div class="agents-label">Agents:</div>
      <div class="agent-bubbles">
        ${agentBubbles}
      </div>
    </div>
  `;
  
  return card;
}

function openVersion(version) {
  selectedVersion = version;
  agentsVersionTitle.textContent = `Version ${version.project_version} - Agents`;
  displayAgents(version);
  showView('agents');
}

function displayAgents(version) {
  agentsList.innerHTML = '';
  
  const agents = getAgentsForVersion(version);
  
  if (agents.length === 0) {
    agentsList.innerHTML = `
      <div class="empty-state">
        <h3>No agents found</h3>
        <p>This version doesn't contain any agents.</p>
      </div>
    `;
    return;
  }
  
  agents.forEach(agent => {
    const agentCard = createAgentCard(agent, version);
    agentsList.appendChild(agentCard);
  });
}

function createAgentCard(agent, version) {
  const card = document.createElement('div');
  card.className = 'agent-card';
  card.onclick = () => openAgentSidebar(agent, version);
  
  card.innerHTML = `
    <div class="agent-header">
      <div class="agent-name">${agent.name}</div>
      <div class="agent-version">v${agent.version}</div>
    </div>
    <div class="agent-description">
      Click to view prompt, system instructions, and execution details
    </div>
  `;
  
  return card;
}

function openAgentSidebar(agent, version) {
  // Populate agent details
  agentTitle.textContent = 'Agent Details';
  agentName.textContent = agent.name;
  agentVersion.textContent = agent.version;
  agentCreated.textContent = new Date(agent.created).toLocaleString();
  agentExecutionTime.textContent = agent.execution_time;
  agentPrompt.textContent = agent.prompt;
  agentSystem.textContent = agent.system;
  
  // Display inputs
  agentInputs.innerHTML = '<strong>Inputs:</strong><br>';
  Object.entries(agent.inputs).forEach(([key, value]) => {
    agentInputs.innerHTML += `${key}: ${value}<br>`;
  });
  
  // Display output
  agentOutput.innerHTML = `<strong>Output:</strong><br>${agent.output}`;
  
  // Show sidebar with animation
  agentSidebar.style.display = 'block';
  setTimeout(() => {
    agentSidebar.classList.add('open');
  }, 10);
}

function closeAgentSidebar() {
  agentSidebar.classList.remove('open');
  setTimeout(() => {
    agentSidebar.style.display = 'none';
  }, 300);
}

function goBackToProjects() {
  selectedProject = null;
  selectedVersion = null;
  showView('projects');
}

function goBackToVersions() {
  selectedVersion = null;
  showView('versions');
}

function filterProjects() {
  const searchTerm = searchInput.value.toLowerCase();
  const projectCards = document.querySelectorAll('.project-card');
  
  projectCards.forEach(card => {
    const projectName = card.querySelector('.project-name').textContent.toLowerCase();
    const isVisible = projectName.includes(searchTerm);
    
    card.style.display = isVisible ? 'block' : 'none';
  });
}

function updateStats() {
  const totalPrompts = runs.reduce((sum, run) => sum + run.total_prompts, 0);
  const totalProjects = new Set(runs.map(run => run.system_name)).size;
  
  if (totalPromptsEl) {
    totalPromptsEl.textContent = totalPrompts;
  }
  
  if (totalProjectsEl) {
    totalProjectsEl.textContent = totalProjects;
  }
}

function getAgentsForVersion(version) {
  // Extract agents from the version's prompts data
  if (version.prompts) {
    return Object.values(version.prompts).map(prompt => ({
      name: prompt.function_name,
      version: prompt.agent_version,
      created: prompt.created_at,
      execution_time: `${prompt.execution_time}s`,
      prompt: prompt.prompt,
      system: prompt.system || 'No system instructions',
      inputs: prompt.inputs || {},
      output: prompt.output || 'No output recorded',
      prompt_data: prompt
    }));
  }
  
  // Fallback to mock data if no prompts
  return [
    { 
      name: 'agent_1', 
      version: '1.0', 
      created: new Date().toISOString(),
      execution_time: '0.123s',
      prompt: `You are a helpful assistant. Process this text: {text}\n\nAgent: agent_1`,
      system: 'You are an AI assistant designed to help users with their tasks.',
      inputs: { text: 'Hello World', agent: 'agent_1' },
      output: 'Processed by agent_1: Hello World',
      prompt_data: null 
    },
    { 
      name: 'agent_2', 
      version: '1.1', 
      created: new Date().toISOString(),
      execution_time: '0.156s',
      prompt: `You are a helpful assistant. Process this text: {text}\n\nAgent: agent_2`,
      system: 'You are an AI assistant designed to help users with their tasks.',
      inputs: { text: 'Hello World', agent: 'agent_2' },
      output: 'Processed by agent_2: Hello World',
      prompt_data: null 
    }
  ];
}

// Make functions globally available
window.goBackToProjects = goBackToProjects;
window.goBackToVersions = goBackToVersions;
window.closeAgentSidebar = closeAgentSidebar;
window.fetchRuns = fetchRuns;