function createJobCard(job)
{return `
<div class="job-card">
<div class="job-header">
<h3 class="job-title">${job.title}</h3>
<p class="company-name">${job.company}</p>
</div>

<div class="job-info">
<span>${job.role}</span>
<span>${job.salary}</span>
<span>${job.type}</span>
</div>

<div class="job-actions">
<a href="job-detail.html" class="details-btn">Ver detalles</a>
<button class="apply-btn">Postularse</button>
</div>

</div>`
}

const jobs = [
{
title:"Desarrollador Web",
company:"Tech RD",
role:"Programador",
salary:"RD$50k - RD$70k",
type:"Tiempo completo"
},

{
title:"Diseñador Gráfico",
company:"Creativa Studio",
role:"Diseñador",
salary:"RD$40k - RD$55k",
type:"Remoto"
},

{
title:"Marketing Digital",
company:"MarketPro",
role:"Especialista SEO",
salary:"RD$45k",
type:"Medio tiempo"
}
]

const container = document.getElementById("jobsContainer")
jobs.forEach(job => {
container.innerHTML += createJobCard(job)
})