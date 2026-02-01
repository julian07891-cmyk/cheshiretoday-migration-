import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Briefcase, MapPin, Clock, Building2, Search, Filter,
  ChevronDown, ExternalLink, Mail, PoundSterling, Star,
  ArrowLeft
} from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';

const getApiUrl = () => {
  if (typeof window !== 'undefined') {
    return process.env.REACT_APP_BACKEND_URL || window.location.origin;
  }
  return '';
};

const JobBoard = () => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedLocation, setSelectedLocation] = useState('all');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedType, setSelectedType] = useState('all');
  const [options, setOptions] = useState({ locations: [], categories: [], job_types: [] });
  const [selectedJob, setSelectedJob] = useState(null);

  useEffect(() => {
    fetchJobs();
    fetchOptions();
  }, []);

  const fetchJobs = async () => {
    try {
      const response = await fetch(`${getApiUrl()}/api/jobs`);
      const data = await response.json();
      if (data.success) {
        setJobs(data.jobs);
      }
    } catch (error) {
      console.error('Error fetching jobs:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchOptions = async () => {
    try {
      const response = await fetch(`${getApiUrl()}/api/jobs/meta/options`);
      const data = await response.json();
      setOptions(data);
    } catch (error) {
      console.error('Error fetching options:', error);
    }
  };

  const filteredJobs = jobs.filter(job => {
    const matchesSearch = job.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          job.company.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesLocation = selectedLocation === 'all' || job.location === selectedLocation;
    const matchesCategory = selectedCategory === 'all' || job.category === selectedCategory;
    const matchesType = selectedType === 'all' || job.job_type === selectedType;
    
    return matchesSearch && matchesLocation && matchesCategory && matchesType;
  });

  const featuredJobs = filteredJobs.filter(job => job.featured);
  const regularJobs = filteredJobs.filter(job => !job.featured);

  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    const now = new Date();
    const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    return date.toLocaleDateString();
  };

  const getTypeColor = (type) => {
    const colors = {
      'Full-time': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      'Part-time': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      'Contract': 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
      'Temporary': 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
      'Remote': 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900 dark:text-cyan-200',
      'Apprenticeship': 'bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-200',
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  // Job Detail View
  if (selectedJob) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="container mx-auto px-4 py-8 max-w-4xl">
          <Button
            variant="ghost"
            onClick={() => setSelectedJob(null)}
            className="mb-6 gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Jobs
          </Button>
          
          <Card className="overflow-hidden">
            <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-6 text-white">
              {selectedJob.featured && (
                <Badge className="bg-yellow-400 text-yellow-900 mb-2">
                  <Star className="h-3 w-3 mr-1" /> Featured
                </Badge>
              )}
              <h1 className="text-2xl md:text-3xl font-bold mb-2">{selectedJob.title}</h1>
              <div className="flex flex-wrap items-center gap-4 text-blue-100">
                <span className="flex items-center gap-1">
                  <Building2 className="h-4 w-4" />
                  {selectedJob.company}
                </span>
                <span className="flex items-center gap-1">
                  <MapPin className="h-4 w-4" />
                  {selectedJob.location}
                </span>
                <Badge className={getTypeColor(selectedJob.job_type)}>
                  {selectedJob.job_type}
                </Badge>
              </div>
            </div>
            
            <CardContent className="p-6 space-y-6">
              {selectedJob.salary && (
                <div className="flex items-center gap-2 text-lg font-semibold text-green-600 dark:text-green-400">
                  <PoundSterling className="h-5 w-5" />
                  {selectedJob.salary}
                </div>
              )}
              
              <div>
                <h3 className="font-semibold text-lg mb-3">Job Description</h3>
                <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                  {selectedJob.description}
                </p>
              </div>
              
              {selectedJob.requirements && (
                <div>
                  <h3 className="font-semibold text-lg mb-3">Requirements</h3>
                  <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                    {selectedJob.requirements}
                  </p>
                </div>
              )}
              
              <div className="flex flex-col sm:flex-row gap-3 pt-4 border-t">
                {selectedJob.apply_url && (
                  <a
                    href={selectedJob.apply_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-1"
                  >
                    <Button className="w-full bg-blue-600 hover:bg-blue-700 gap-2">
                      <ExternalLink className="h-4 w-4" />
                      Apply Online
                    </Button>
                  </a>
                )}
                {selectedJob.apply_email && (
                  <a
                    href={`mailto:${selectedJob.apply_email}?subject=Application for ${selectedJob.title}`}
                    className="flex-1"
                  >
                    <Button variant="outline" className="w-full gap-2">
                      <Mail className="h-4 w-4" />
                      Email Application
                    </Button>
                  </a>
                )}
              </div>
              
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Posted {formatDate(selectedJob.created_at)} • Category: {selectedJob.category}
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white">
        <div className="container mx-auto px-4 py-12">
          <Link to="/" className="inline-flex items-center gap-2 text-blue-100 hover:text-white mb-4">
            <ArrowLeft className="h-4 w-4" />
            Back to News
          </Link>
          <div className="flex items-center gap-3 mb-4">
            <Briefcase className="h-10 w-10" />
            <div>
              <h1 className="text-3xl md:text-4xl font-bold">Cheshire Jobs</h1>
              <p className="text-blue-100">Find your next opportunity in Cheshire</p>
            </div>
          </div>
          
          {/* Search Bar */}
          <div className="mt-6 max-w-2xl">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
              <Input
                type="text"
                placeholder="Search jobs by title or company..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-12 h-12 text-gray-900 text-lg rounded-full"
              />
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        {/* Filters */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-md mb-6">
          <div className="flex flex-wrap items-center gap-4">
            <Filter className="h-5 w-5 text-gray-500" />
            
            <Select value={selectedLocation} onValueChange={setSelectedLocation}>
              <SelectTrigger className="w-[160px]">
                <SelectValue placeholder="Location" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Locations</SelectItem>
                {options.locations.map(loc => (
                  <SelectItem key={loc} value={loc}>{loc}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            <Select value={selectedCategory} onValueChange={setSelectedCategory}>
              <SelectTrigger className="w-[160px]">
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                {options.categories.map(cat => (
                  <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            <Select value={selectedType} onValueChange={setSelectedType}>
              <SelectTrigger className="w-[160px]">
                <SelectValue placeholder="Job Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                {options.job_types.map(type => (
                  <SelectItem key={type} value={type}>{type}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            <span className="text-sm text-gray-500 ml-auto">
              {filteredJobs.length} job{filteredJobs.length !== 1 ? 's' : ''} found
            </span>
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : filteredJobs.length === 0 ? (
          <Card className="text-center py-12">
            <Briefcase className="h-16 w-16 mx-auto text-gray-300 mb-4" />
            <h3 className="text-xl font-semibold text-gray-600 dark:text-gray-400">No jobs found</h3>
            <p className="text-gray-500 mt-2">Try adjusting your filters or search terms</p>
          </Card>
        ) : (
          <div className="space-y-6">
            {/* Featured Jobs */}
            {featuredJobs.length > 0 && (
              <div>
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <Star className="h-5 w-5 text-yellow-500" />
                  Featured Jobs
                </h2>
                <div className="grid gap-4">
                  {featuredJobs.map(job => (
                    <Card
                      key={job.id}
                      className="cursor-pointer hover:shadow-lg transition-shadow border-2 border-yellow-200 dark:border-yellow-800 bg-gradient-to-r from-yellow-50 to-white dark:from-yellow-900/20 dark:to-gray-800"
                      onClick={() => setSelectedJob(job)}
                    >
                      <CardContent className="p-5">
                        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                          <div className="flex-1">
                            <div className="flex items-start gap-3">
                              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center text-white font-bold text-lg flex-shrink-0">
                                {job.company.charAt(0)}
                              </div>
                              <div>
                                <h3 className="font-bold text-lg text-gray-900 dark:text-white hover:text-blue-600">
                                  {job.title}
                                </h3>
                                <p className="text-gray-600 dark:text-gray-400 flex items-center gap-1">
                                  <Building2 className="h-4 w-4" />
                                  {job.company}
                                </p>
                              </div>
                            </div>
                          </div>
                          
                          <div className="flex flex-wrap items-center gap-2">
                            <Badge variant="outline" className="flex items-center gap-1">
                              <MapPin className="h-3 w-3" />
                              {job.location}
                            </Badge>
                            <Badge className={getTypeColor(job.job_type)}>
                              {job.job_type}
                            </Badge>
                            {job.salary && (
                              <Badge variant="outline" className="text-green-600 border-green-200">
                                {job.salary}
                              </Badge>
                            )}
                          </div>
                        </div>
                        <p className="text-sm text-gray-500 mt-3">
                          Posted {formatDate(job.created_at)} • {job.category}
                        </p>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            )}

            {/* Regular Jobs */}
            {regularJobs.length > 0 && (
              <div>
                {featuredJobs.length > 0 && (
                  <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                    All Jobs
                  </h2>
                )}
                <div className="grid gap-4">
                  {regularJobs.map(job => (
                    <Card
                      key={job.id}
                      className="cursor-pointer hover:shadow-lg transition-shadow"
                      onClick={() => setSelectedJob(job)}
                    >
                      <CardContent className="p-5">
                        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                          <div className="flex-1">
                            <div className="flex items-start gap-3">
                              <div className="w-12 h-12 bg-gray-200 dark:bg-gray-700 rounded-lg flex items-center justify-center text-gray-600 dark:text-gray-300 font-bold text-lg flex-shrink-0">
                                {job.company.charAt(0)}
                              </div>
                              <div>
                                <h3 className="font-bold text-lg text-gray-900 dark:text-white hover:text-blue-600">
                                  {job.title}
                                </h3>
                                <p className="text-gray-600 dark:text-gray-400 flex items-center gap-1">
                                  <Building2 className="h-4 w-4" />
                                  {job.company}
                                </p>
                              </div>
                            </div>
                          </div>
                          
                          <div className="flex flex-wrap items-center gap-2">
                            <Badge variant="outline" className="flex items-center gap-1">
                              <MapPin className="h-3 w-3" />
                              {job.location}
                            </Badge>
                            <Badge className={getTypeColor(job.job_type)}>
                              {job.job_type}
                            </Badge>
                            {job.salary && (
                              <Badge variant="outline" className="text-green-600 border-green-200">
                                {job.salary}
                              </Badge>
                            )}
                          </div>
                        </div>
                        <p className="text-sm text-gray-500 mt-3">
                          Posted {formatDate(job.created_at)} • {job.category}
                        </p>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Post a Job CTA */}
        <Card className="mt-8 bg-gradient-to-r from-emerald-500 to-teal-600 text-white">
          <CardContent className="p-6 text-center">
            <h3 className="text-xl font-bold mb-2">Looking to Hire?</h3>
            <p className="text-emerald-100 mb-4">
              Post your job listing and reach thousands of Cheshire job seekers
            </p>
            <Link to="/jobs/post">
              <Button className="bg-white text-emerald-600 hover:bg-emerald-50" data-testid="post-job-cta">
                Post a Job - Free
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default JobBoard;
