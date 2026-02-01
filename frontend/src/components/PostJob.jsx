import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  Briefcase, Building2, MapPin, Mail, Phone, User,
  ArrowLeft, Send, CheckCircle, Loader2, PoundSterling,
  FileText, Link as LinkIcon, CreditCard, Star, Clock,
  Check
} from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Label } from './ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';
import { toast } from '../hooks/use-toast';
import { Badge } from './ui/badge';

const getApiUrl = () => {
  if (typeof window !== 'undefined') {
    return process.env.REACT_APP_BACKEND_URL || window.location.origin;
  }
  return '';
};

const PostJob = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(1); // 1: Form, 2: Payment
  const [submitting, setSubmitting] = useState(false);
  const [options, setOptions] = useState({ locations: [], categories: [], job_types: [] });
  const [selectedPackage, setSelectedPackage] = useState('free');
  
  // Default packages - always available even if API fails
  const defaultPackages = [
    {
      id: "free",
      name: "Free Listing",
      price: 0,
      description: "14-day basic listing",
      features: ["14 days", "Basic listing", "No payment"]
    },
    {
      id: "standard",
      name: "Standard",
      price: 15,
      description: "30-day listing",
      features: ["30 days", "Email support"]
    },
    {
      id: "featured",
      name: "Featured",
      price: 29,
      description: "30-day featured listing",
      features: ["30 days", "Featured badge", "Top placement"]
    },
    {
      id: "premium",
      name: "Premium",
      price: 49,
      description: "60-day premium listing",
      features: ["60 days", "Featured", "Social promo"]
    }
  ];
  
  const [packages, setPackages] = useState(defaultPackages);
  
  const [formData, setFormData] = useState({
    title: '',
    company: '',
    location: 'Macclesfield',
    job_type: 'Full-time',
    salary: '',
    description: '',
    requirements: '',
    category: 'Other',
    apply_url: '',
    apply_email: '',
    contact_name: '',
    contact_email: '',
    contact_phone: ''
  });

  useEffect(() => {
    fetchOptions();
    fetchPackages();
  }, []);

  const fetchOptions = async () => {
    try {
      const response = await fetch(`${getApiUrl()}/api/jobs/meta/options`);
      const data = await response.json();
      setOptions(data);
    } catch (error) {
      console.error('Error fetching options:', error);
    }
  };

  const fetchPackages = async () => {
    try {
      const response = await fetch(`${getApiUrl()}/api/jobs/packages`);
      const data = await response.json();
      if (data.packages && data.packages.length > 0) {
        setPackages(data.packages);
      }
      // If no packages returned, keep the defaults
    } catch (error) {
      console.error('Error fetching packages:', error);
      // Keep default packages on error
    }
  };

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleContinueToPayment = (e) => {
    e.preventDefault();
    
    // Validation
    if (!formData.title || !formData.company || !formData.description || !formData.contact_name || !formData.contact_email) {
      toast({
        title: "Missing Required Fields",
        description: "Please fill in all required fields (marked with *)",
        variant: "destructive"
      });
      return;
    }

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.contact_email)) {
      toast({
        title: "Invalid Email",
        description: "Please enter a valid contact email address",
        variant: "destructive"
      });
      return;
    }

    setStep(2);
  };

  const handlePayment = async () => {
    // Validation
    if (!formData.title || !formData.company || !formData.description || !formData.contact_name || !formData.contact_email) {
      toast({
        title: "Missing Required Fields",
        description: "Please fill in all required fields (Job Title, Company, Description, Your Name, Email)",
        variant: "destructive"
      });
      return;
    }

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.contact_email)) {
      toast({
        title: "Invalid Email",
        description: "Please enter a valid contact email address",
        variant: "destructive"
      });
      return;
    }
    
    setSubmitting(true);
    console.log('[PostJob] Starting payment flow for package:', selectedPackage);
    
    try {
      const apiUrl = getApiUrl();
      console.log('[PostJob] API URL:', apiUrl);
      console.log('[PostJob] Sending checkout request...');
      
      const requestBody = {
        package_id: selectedPackage,
        origin_url: window.location.origin,
        ...formData
      };
      console.log('[PostJob] Request body:', JSON.stringify(requestBody, null, 2));
      
      const response = await fetch(`${apiUrl}/api/jobs/checkout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });
      
      console.log('[PostJob] Response status:', response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('[PostJob] Response error:', errorText);
        throw new Error(`Server error (${response.status}): ${errorText}`);
      }
      
      const data = await response.json();
      console.log('[PostJob] Response data:', data);
      
      if (data.success) {
        // Handle FREE listing - no payment needed
        if (data.free_listing) {
          console.log('[PostJob] Free listing submitted successfully');
          toast({
            title: "Job Submitted!",
            description: "Your free listing is pending review"
          });
          navigate('/jobs/payment-success?free=true');
          return;
        }
        
        // Paid listing - redirect to Stripe checkout
        if (data.checkout_url) {
          console.log('[PostJob] Redirecting to Stripe:', data.checkout_url);
          // Use window.location.href for maximum compatibility
          window.location.href = data.checkout_url;
          return;
        } else {
          console.error('[PostJob] No checkout URL in response');
          throw new Error('No checkout URL received from server');
        }
      } else {
        console.error('[PostJob] API returned success=false:', data);
        throw new Error(data.detail || data.message || 'Failed to create checkout session');
      }
    } catch (error) {
      console.error('[PostJob] Payment error:', error);
      toast({
        title: "Payment Error",
        description: error.message || "Failed to submit job listing. Please try again.",
        variant: "destructive"
      });
      setSubmitting(false);
    }
  };

  const selectedPkg = packages.find(p => p.id === selectedPackage);

  // Step 2: Payment Selection
  if (step === 2) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        {/* Header */}
        <div className="bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-600 text-white">
          <div className="container mx-auto px-4 py-10">
            <button 
              onClick={() => setStep(1)} 
              className="inline-flex items-center gap-2 text-emerald-100 hover:text-white mb-4"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Details
            </button>
            <div className="flex items-center gap-3">
              <CreditCard className="h-10 w-10" />
              <div>
                <h1 className="text-3xl md:text-4xl font-bold">Choose Your Plan</h1>
                <p className="text-emerald-100">Select a package to reach Cheshire job seekers</p>
              </div>
            </div>
          </div>
        </div>

        <div className="container mx-auto px-4 py-8 max-w-4xl">
          {/* Job Summary */}
          <Card className="mb-6 bg-gray-50 dark:bg-gray-800">
            <CardContent className="pt-6">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center text-white font-bold text-lg flex-shrink-0">
                  {formData.company.charAt(0)}
                </div>
                <div>
                  <h3 className="font-bold text-lg text-gray-900 dark:text-white">{formData.title}</h3>
                  <p className="text-gray-600 dark:text-gray-400">{formData.company} • {formData.location}</p>
                  <p className="text-sm text-gray-500 mt-1">{formData.job_type} • {formData.category}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Packages */}
          <div className="grid md:grid-cols-4 gap-4 mb-6">
            {packages.map((pkg) => {
              const isSelected = selectedPackage === pkg.id;
              return (
                <div
                  key={pkg.id}
                  onClick={() => setSelectedPackage(pkg.id)}
                  className={`relative cursor-pointer rounded-xl transition-all duration-200 ${
                    isSelected 
                      ? 'ring-4 ring-emerald-500 shadow-lg shadow-emerald-500/20 scale-[1.02]' 
                      : 'ring-1 ring-gray-200 dark:ring-gray-700 hover:ring-gray-300 dark:hover:ring-gray-600 hover:shadow-md'
                  }`}
                >
                  {/* Selected Indicator Banner */}
                  {isSelected && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2 z-10">
                      <div className="bg-emerald-500 text-white text-xs font-bold px-4 py-1 rounded-full flex items-center gap-1 shadow-lg">
                        <Check className="h-3 w-3" />
                        SELECTED
                      </div>
                    </div>
                  )}
                  
                  {/* Popular/Free Badge */}
                  {!isSelected && pkg.id === 'featured' && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2 z-10">
                      <Badge className="bg-amber-500 text-white shadow">Most Popular</Badge>
                    </div>
                  )}
                  {!isSelected && pkg.id === 'free' && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2 z-10">
                      <Badge className="bg-green-500 text-white shadow">Free</Badge>
                    </div>
                  )}
                  
                  <div className={`p-5 rounded-xl ${
                    isSelected 
                      ? 'bg-emerald-50 dark:bg-emerald-900/30' 
                      : pkg.id === 'free' 
                        ? 'bg-green-50/50 dark:bg-green-900/10' 
                        : 'bg-white dark:bg-gray-800'
                  }`}>
                    {/* Header */}
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className={`font-bold text-lg ${isSelected ? 'text-emerald-700 dark:text-emerald-300' : 'text-gray-900 dark:text-white'}`}>
                          {pkg.name}
                        </h3>
                        <div className={`text-3xl font-bold mt-1 ${isSelected ? 'text-emerald-600 dark:text-emerald-400' : 'text-gray-900 dark:text-white'}`}>
                          {pkg.price === 0 ? 'Free' : `£${pkg.price}`}
                        </div>
                      </div>
                      
                      {/* Radio-style indicator */}
                      <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center flex-shrink-0 transition-all ${
                        isSelected 
                          ? 'bg-emerald-500 border-emerald-500' 
                          : 'border-gray-300 dark:border-gray-600'
                      }`}>
                        {isSelected && <Check className="h-4 w-4 text-white" />}
                      </div>
                    </div>
                    
                    {/* Description */}
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                      {pkg.description}
                    </p>
                    
                    {/* Features */}
                    <ul className="space-y-2">
                      {pkg.features.map((feature, idx) => (
                        <li key={idx} className="flex items-center gap-2 text-sm">
                          <Check className={`h-4 w-4 flex-shrink-0 ${isSelected ? 'text-emerald-600' : 'text-emerald-500'}`} />
                          <span className={isSelected ? 'text-emerald-800 dark:text-emerald-200' : 'text-gray-700 dark:text-gray-300'}>
                            {feature}
                          </span>
                        </li>
                      ))}
                    </ul>
                    
                    {/* Select Button */}
                    <button className={`w-full mt-4 py-2 px-4 rounded-lg font-medium transition-all ${
                      isSelected 
                        ? 'bg-emerald-600 text-white' 
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                    }`}>
                      {isSelected ? '✓ Selected' : 'Select'}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Payment Button */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <p className="text-sm text-gray-500">Selected Package</p>
                  <p className="font-semibold text-lg">{selectedPkg?.name}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-500">Total</p>
                  <p className="text-2xl font-bold text-emerald-600">
                    {selectedPkg?.price === 0 ? 'Free' : `£${selectedPkg?.price}`}
                  </p>
                </div>
              </div>
              
              <Button 
                onClick={handlePayment}
                className="w-full bg-emerald-600 hover:bg-emerald-700 h-14 text-lg gap-2"
                disabled={submitting}
                data-testid="pay-now-button"
              >
                {submitting ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin" />
                    {selectedPkg?.price === 0 ? 'Submitting...' : 'Processing...'}
                  </>
                ) : selectedPkg?.price === 0 ? (
                  <>
                    <Send className="h-5 w-5" />
                    Submit Free Listing
                  </>
                ) : (
                  <>
                    <CreditCard className="h-5 w-5" />
                    Pay £{selectedPkg?.price} & Submit Job
                  </>
                )}
              </Button>
              
              <div className="flex items-center justify-center gap-4 mt-4 text-sm text-gray-500">
                <span className="flex items-center gap-1">
                  <svg className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z"/>
                  </svg>
                  Secure Payment
                </span>
                <span>Powered by Stripe</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // Step 1: Job Details Form
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-600 text-white">
        <div className="container mx-auto px-4 py-10">
          <Link to="/jobs" className="inline-flex items-center gap-2 text-emerald-100 hover:text-white mb-4">
            <ArrowLeft className="h-4 w-4" />
            Back to Jobs
          </Link>
          <div className="flex items-center gap-3">
            <Briefcase className="h-10 w-10" />
            <div>
              <h1 className="text-3xl md:text-4xl font-bold">Post a Job</h1>
              <p className="text-emerald-100">Reach thousands of Cheshire job seekers</p>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8 max-w-3xl">
        {/* Package Selection - Clickable Cards */}
        <div className="mb-6">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
            <Star className="h-5 w-5 text-emerald-600" />
            Choose Your Package
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {packages.map((pkg) => {
              const isSelected = selectedPackage === pkg.id;
              return (
                <button
                  key={pkg.id}
                  type="button"
                  onClick={() => setSelectedPackage(pkg.id)}
                  className={`relative p-4 rounded-xl text-left transition-all ${
                    isSelected 
                      ? 'bg-emerald-600 text-white ring-4 ring-emerald-300 shadow-lg' 
                      : 'bg-white dark:bg-gray-800 border-2 border-gray-200 dark:border-gray-700 hover:border-emerald-400'
                  }`}
                >
                  {isSelected && (
                    <div className="absolute -top-2 -right-2 w-6 h-6 bg-white rounded-full flex items-center justify-center shadow">
                      <Check className="h-4 w-4 text-emerald-600" />
                    </div>
                  )}
                  <div className={`text-xs font-medium mb-1 ${isSelected ? 'text-emerald-100' : 'text-gray-500'}`}>
                    {pkg.id === 'free' ? '14 days' : pkg.id === 'premium' ? '60 days' : '30 days'}
                  </div>
                  <div className={`font-bold text-lg ${isSelected ? 'text-white' : 'text-gray-900 dark:text-white'}`}>
                    {pkg.price === 0 ? 'Free' : `£${pkg.price}`}
                  </div>
                  <div className={`text-sm ${isSelected ? 'text-emerald-100' : 'text-gray-600 dark:text-gray-400'}`}>
                    {pkg.name}
                  </div>
                  {pkg.id === 'featured' && !isSelected && (
                    <span className="absolute -top-2 left-2 bg-amber-500 text-white text-xs px-2 py-0.5 rounded-full">
                      Popular
                    </span>
                  )}
                </button>
              );
            })}
          </div>
          <p className="text-sm text-gray-500 mt-2 text-center">
            {selectedPackage === 'free' ? '✓ Free listing selected - no payment needed!' : `Selected: ${selectedPkg?.name} (£${selectedPkg?.price})`}
          </p>
        </div>

        {/* Form */}
        <Card>
          <CardHeader>
            <CardTitle>Job Details</CardTitle>
            <CardDescription>Fill in the details below • Fields marked with * are required</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleContinueToPayment} className="space-y-6">
              {/* Job Info Section */}
              <div className="space-y-4">
                <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                  <Briefcase className="h-4 w-4 text-emerald-600" />
                  Position Information
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="title">Job Title *</Label>
                    <Input
                      id="title"
                      value={formData.title}
                      onChange={(e) => handleChange('title', e.target.value)}
                      placeholder="e.g. Marketing Manager"
                      required
                      data-testid="post-job-title"
                    />
                  </div>
                  <div>
                    <Label htmlFor="company">Company Name *</Label>
                    <Input
                      id="company"
                      value={formData.company}
                      onChange={(e) => handleChange('company', e.target.value)}
                      placeholder="e.g. Acme Ltd"
                      required
                      data-testid="post-job-company"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <Label htmlFor="location">Location *</Label>
                    <Select value={formData.location} onValueChange={(val) => handleChange('location', val)}>
                      <SelectTrigger data-testid="post-job-location">
                        <SelectValue placeholder="Select location" />
                      </SelectTrigger>
                      <SelectContent>
                        {(options.locations.length > 0 ? options.locations : ['Macclesfield', 'Chester', 'Crewe', 'Warrington', 'Wilmslow']).map(loc => (
                          <SelectItem key={loc} value={loc}>{loc}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="job_type">Job Type *</Label>
                    <Select value={formData.job_type} onValueChange={(val) => handleChange('job_type', val)}>
                      <SelectTrigger data-testid="post-job-type">
                        <SelectValue placeholder="Select type" />
                      </SelectTrigger>
                      <SelectContent>
                        {(options.job_types.length > 0 ? options.job_types : ['Full-time', 'Part-time', 'Contract', 'Remote']).map(type => (
                          <SelectItem key={type} value={type}>{type}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="category">Category *</Label>
                    <Select value={formData.category} onValueChange={(val) => handleChange('category', val)}>
                      <SelectTrigger data-testid="post-job-category">
                        <SelectValue placeholder="Select category" />
                      </SelectTrigger>
                      <SelectContent>
                        {(options.categories.length > 0 ? options.categories : ['IT & Technology', 'Healthcare', 'Retail', 'Other']).map(cat => (
                          <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div>
                  <Label htmlFor="salary">
                    <PoundSterling className="h-4 w-4 inline mr-1" />
                    Salary (optional but recommended)
                  </Label>
                  <Input
                    id="salary"
                    value={formData.salary}
                    onChange={(e) => handleChange('salary', e.target.value)}
                    placeholder="e.g. £30,000 - £40,000 or Competitive"
                    data-testid="post-job-salary"
                  />
                  <p className="text-xs text-gray-500 mt-1">Jobs with salary info get 30% more applications</p>
                </div>

                <div>
                  <Label htmlFor="description">Job Description *</Label>
                  <Textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) => handleChange('description', e.target.value)}
                    placeholder="Describe the role, responsibilities, what makes this opportunity exciting..."
                    rows={5}
                    required
                    data-testid="post-job-description"
                  />
                </div>

                <div>
                  <Label htmlFor="requirements">Requirements (optional)</Label>
                  <Textarea
                    id="requirements"
                    value={formData.requirements}
                    onChange={(e) => handleChange('requirements', e.target.value)}
                    placeholder="List skills, qualifications, or experience required..."
                    rows={3}
                    data-testid="post-job-requirements"
                  />
                </div>
              </div>

              {/* Application Methods */}
              <div className="space-y-4 pt-4 border-t">
                <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                  <LinkIcon className="h-4 w-4 text-emerald-600" />
                  How to Apply (provide at least one)
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="apply_url">Application URL</Label>
                    <Input
                      id="apply_url"
                      type="url"
                      value={formData.apply_url}
                      onChange={(e) => handleChange('apply_url', e.target.value)}
                      placeholder="https://yourcompany.com/careers/apply"
                      data-testid="post-job-apply-url"
                    />
                  </div>
                  <div>
                    <Label htmlFor="apply_email">Application Email</Label>
                    <Input
                      id="apply_email"
                      type="email"
                      value={formData.apply_email}
                      onChange={(e) => handleChange('apply_email', e.target.value)}
                      placeholder="hr@yourcompany.com"
                      data-testid="post-job-apply-email"
                    />
                  </div>
                </div>
              </div>

              {/* Contact Info */}
              <div className="space-y-4 pt-4 border-t">
                <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                  <User className="h-4 w-4 text-emerald-600" />
                  Your Contact Details (for approval notifications)
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  This information is only used to notify you about your listing status. It will not be displayed publicly.
                </p>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="contact_name">Your Name *</Label>
                    <Input
                      id="contact_name"
                      value={formData.contact_name}
                      onChange={(e) => handleChange('contact_name', e.target.value)}
                      placeholder="John Smith"
                      required
                      data-testid="post-job-contact-name"
                    />
                  </div>
                  <div>
                    <Label htmlFor="contact_email">Your Email *</Label>
                    <Input
                      id="contact_email"
                      type="email"
                      value={formData.contact_email}
                      onChange={(e) => handleChange('contact_email', e.target.value)}
                      placeholder="john@company.com"
                      required
                      data-testid="post-job-contact-email"
                    />
                  </div>
                </div>
                <div className="md:w-1/2">
                  <Label htmlFor="contact_phone">Phone (optional)</Label>
                  <Input
                    id="contact_phone"
                    type="tel"
                    value={formData.contact_phone}
                    onChange={(e) => handleChange('contact_phone', e.target.value)}
                    placeholder="01onal 123456"
                    data-testid="post-job-contact-phone"
                  />
                </div>
              </div>

              {/* Submit Button */}
              <div className="pt-4 border-t">
                <Button 
                  type="button"
                  onClick={handlePayment}
                  disabled={submitting}
                  className="w-full bg-emerald-600 hover:bg-emerald-700 h-14 text-lg gap-2"
                  data-testid="submit-job-button"
                >
                  {submitting ? (
                    <>
                      <Loader2 className="h-5 w-5 animate-spin" />
                      Submitting...
                    </>
                  ) : selectedPackage === 'free' ? (
                    <>
                      <Send className="h-5 w-5" />
                      Submit Free Listing
                    </>
                  ) : (
                    <>
                      <CreditCard className="h-5 w-5" />
                      Pay £{selectedPkg?.price} & Submit
                    </>
                  )}
                </Button>
                <p className="text-xs text-center text-gray-500 mt-3">
                  {selectedPackage === 'free' 
                    ? 'Your free listing will be reviewed within 1-2 days' 
                    : 'You\'ll be redirected to secure Stripe checkout'}
                </p>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default PostJob;
