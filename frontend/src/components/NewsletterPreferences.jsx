import React from "react";
import { Link } from "react-router-dom";
import { CheckCircle, Mail } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "./ui/dialog";
import { Button } from "./ui/button";

const NewsletterPreferences = ({ open, onOpenChange }) => (
  <Dialog open={open} onOpenChange={onOpenChange}>
    <DialogContent className="max-w-md">
      <DialogHeader>
        <DialogTitle className="flex items-center gap-2">
          <CheckCircle className="h-5 w-5 text-emerald-600" aria-hidden="true" />
          Newsletter signup received
        </DialogTitle>
        <DialogDescription>
          Your signup request has been processed. Newsletter preferences are
          managed only through secure email links.
        </DialogDescription>
      </DialogHeader>
      <div className="rounded-lg border border-gray-200 p-4 text-sm text-gray-700 dark:border-gray-700 dark:text-gray-300">
        <Mail className="mb-2 h-5 w-5 text-blue-600" aria-hidden="true" />
        To review your choices, request a secure preferences link on the
        newsletter management page.
      </div>
      <DialogFooter className="gap-2">
        <Button variant="outline" onClick={() => onOpenChange(false)}>
          Close
        </Button>
        <Button asChild className="bg-emerald-600 hover:bg-emerald-700">
          <Link to="/newsletter/preferences">Manage securely</Link>
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
);

export default NewsletterPreferences;
