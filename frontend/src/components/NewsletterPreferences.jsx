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
import {
  NEWSLETTER_CREATED_ITEMS,
  NEWSLETTER_CREATED_LEAD,
  NEWSLETTER_CREATED_SUPPORT,
  NEWSLETTER_CREATED_TITLE,
  NEWSLETTER_EXISTING_MESSAGE,
} from "../constants/newsletterSignup";

const NewsletterPreferences = ({ open, onOpenChange, outcome = "existing" }) => {
  const created = outcome === "created";

  return (
  <Dialog open={open} onOpenChange={onOpenChange}>
    <DialogContent className="max-w-md">
      <DialogHeader>
        <DialogTitle className="flex items-center gap-2">
          <CheckCircle className="h-5 w-5 text-emerald-600" aria-hidden="true" />
          {created ? NEWSLETTER_CREATED_TITLE : "Newsletter signup received"}
        </DialogTitle>
        <DialogDescription>
          {created
            ? NEWSLETTER_CREATED_SUPPORT
            : NEWSLETTER_EXISTING_MESSAGE}
        </DialogDescription>
      </DialogHeader>
      <div className="rounded-lg border border-gray-200 p-4 text-sm text-gray-700 dark:border-gray-700 dark:text-gray-300">
        {created ? (
          <>
            <p className="mb-2 font-semibold">{NEWSLETTER_CREATED_LEAD}</p>
            <ul className="list-disc space-y-1 pl-5">
              {NEWSLETTER_CREATED_ITEMS.map((item) => <li key={item}>{item}</li>)}
            </ul>
          </>
        ) : (
          <>
            <Mail className="mb-2 h-5 w-5 text-blue-600" aria-hidden="true" />
            Use secure newsletter management if you need to review an existing
            subscription, change preferences or reactivate.
          </>
        )}
      </div>
      <DialogFooter className="gap-2">
        <Button asChild variant="outline">
          <Link to="/newsletter/preferences">Manage preferences</Link>
        </Button>
        <Button className="bg-emerald-600 hover:bg-emerald-700" onClick={() => onOpenChange(false)}>
          Close
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
  );
};

export default NewsletterPreferences;
