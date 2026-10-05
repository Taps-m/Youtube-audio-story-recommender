import unittest
import fit_preferences as model

class PreferenceRegression(unittest.TestCase):
 def test_author_is_not_series(self):
  s=model.enrich('sample','Biswa Mitra Upakhyan | Abhik Arjun Dutta | Romantic Premer Golpo','Kahon',{})
  self.assertNotIn('Arjun',s['series'])
  self.assertNotIn('Samaresh Majumdar',s['authors'])
  self.assertNotIn('detective mystery',s['genres'])
 def test_series_segment(self):
  for title in ['Arjun | Hishebe Bhul Chhilo | Samaresh Majumdar','অর্জুন | একটি গল্প']:
   self.assertIn('Arjun',model.enrich('sample',title,'channel',{})['series'])
 def test_timing_excluded_from_features(self):
  self.assertEqual(model.FEATURES,['return_days','recency'])
  self.assertNotIn('completion',model.PRIORS)
  self.assertNotIn('skip_rate',model.PRIORS)
  self.assertNotIn('bt_preference',model.PRIORS)

if __name__=='__main__':unittest.main()
