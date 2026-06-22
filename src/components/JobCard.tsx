import { MapPin, Briefcase, GraduationCap, Clock } from 'lucide-react';
import type { Job } from '../types/job';
import { formatRelativeDate } from '../utils';

interface JobCardProps {
  job: Job;
  onClick: (job: Job) => void;
}

export function JobCard({ job, onClick }: JobCardProps) {
  return (
    <div
      className={`job-card${job.featured ? ' featured' : ''}`}
      onClick={() => onClick(job)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onClick(job)}
    >
      <div className="job-card-company-logo">
        {job.companyLogo ? (
          <img src={job.companyLogo} alt={`${job.company} logo`} />
        ) : (
          job.company.charAt(0)
        )}
      </div>

      <div className="job-card-content">
        <div className="job-card-title">{job.title}</div>
        <div className="job-card-company">{job.company}</div>

        <div className="job-card-meta">
          <span className="job-card-tag salary">
            <Briefcase size={12} />
            {job.salary}
          </span>
          <span className="job-card-tag">
            <MapPin size={12} />
            {job.city}
          </span>
          <span className="job-card-tag">
            <GraduationCap size={12} />
            {job.education}
          </span>
          <span className="job-card-tag">
            <Clock size={12} />
            {formatRelativeDate(job.postedAt)}
          </span>
          {job.tags.slice(0, 2).map((tag) => (
            <span key={tag} className="job-card-tag">
              {tag}
            </span>
          ))}
        </div>
      </div>

      <div className="job-card-side">
        {job.featured && <span className="job-card-featured-badge">推荐</span>}
      </div>
    </div>
  );
}
