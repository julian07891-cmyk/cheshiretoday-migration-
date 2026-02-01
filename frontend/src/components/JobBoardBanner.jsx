import React from 'react';
import { Link } from 'react-router-dom';
import { Briefcase, ArrowRight, Users, MapPin } from 'lucide-react';
import { Button } from './ui/button';

export const JobBoardBanner = () => {
  return (
    <div className="my-8 rounded-2xl overflow-hidden bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-600 shadow-lg">
      <div className="px-6 py-8 md:px-10 md:py-10">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          {/* Left Content */}
          <div className="flex-1 text-center md:text-left">
            <div className="inline-flex items-center gap-2 bg-white/20 backdrop-blur-sm px-3 py-1 rounded-full text-white text-sm mb-4">
              <Briefcase className="h-4 w-4" />
              <span>Cheshire Jobs</span>
            </div>
            <h3 className="text-2xl md:text-3xl font-bold text-white mb-2">
              Find Your Next Opportunity
            </h3>
            <p className="text-emerald-100 text-lg mb-4">
              Browse local jobs across Cheshire or post your vacancy
            </p>
            <div className="flex flex-wrap items-center justify-center md:justify-start gap-4 text-emerald-100 text-sm">
              <span className="flex items-center gap-1">
                <MapPin className="h-4 w-4" />
                Local Cheshire Jobs
              </span>
              <span className="flex items-center gap-1">
                <Users className="h-4 w-4" />
                1000s of Job Seekers
              </span>
            </div>
          </div>
          
          {/* Right Buttons */}
          <div className="flex flex-col sm:flex-row gap-3">
            <Link to="/jobs">
              <Button 
                className="bg-white text-emerald-700 hover:bg-emerald-50 font-semibold px-6 h-12 gap-2 shadow-md"
                data-testid="homepage-browse-jobs"
              >
                Browse Jobs
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link to="/jobs/post">
              <Button 
                variant="outline" 
                className="border-2 border-white text-white hover:bg-white/10 font-semibold px-6 h-12"
                data-testid="homepage-post-job"
              >
                Post a Job
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export const JobBoardBannerCompact = () => {
  return (
    <Link to="/jobs" className="block my-6">
      <div className="rounded-xl overflow-hidden bg-gradient-to-r from-emerald-600 to-teal-600 shadow-md hover:shadow-lg transition-shadow">
        <div className="px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
              <Briefcase className="h-5 w-5 text-white" />
            </div>
            <div>
              <h4 className="font-semibold text-white">Cheshire Jobs</h4>
              <p className="text-emerald-100 text-sm">Find local opportunities</p>
            </div>
          </div>
          <ArrowRight className="h-5 w-5 text-white" />
        </div>
      </div>
    </Link>
  );
};

export default JobBoardBanner;
